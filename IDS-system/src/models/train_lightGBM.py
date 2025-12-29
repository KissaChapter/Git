# train_lightgbm_stratified.py - 使用预分割数据训练模型
import lightgbm as lgb
import numpy as np
from pathlib import Path
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, precision_recall_curve, auc
import json
import matplotlib.pyplot as plt
import seaborn as sns
plt.rcParams['font.family'] = 'sans-serif'           # 告诉 matplotlib 使用 sans-serif 族
plt.rcParams['font.sans-serif'] = ['SimHei']         # 把默认西文字体换成黑体（Windows 自带）
plt.rcParams['axes.unicode_minus'] = False           # 解决负号“-”显示为方块的问题

def load_data(data_dir, max_train_samples=None):
    """加载预分割的训练集和测试集"""
    print("加载数据...")

    X_train = np.load(data_dir / 'X_train.npy', mmap_mode='r')
    y_train = np.load(data_dir / 'y_train.npy', mmap_mode='r')
    X_test = np.load(data_dir / 'X_test.npy', mmap_mode='r')
    y_test = np.load(data_dir / 'y_test.npy', mmap_mode='r')

    print(f"训练集: X{X_train.shape}, y{y_train.shape}")
    print(f"测试集: X{X_test.shape}, y{y_test.shape}")

    # 如果训练集太大，可以进一步采样
    if max_train_samples and len(X_train) > max_train_samples:
        print(f"\n训练集采样: {max_train_samples:,} / {len(X_train):,}")

        # 分层采样
        normal_indices = np.where(y_train == 0)[0]
        attack_indices = np.where(y_train == 1)[0]

        normal_ratio = len(normal_indices) / len(y_train)
        normal_sample_size = int(max_train_samples * normal_ratio)
        attack_sample_size = max_train_samples - normal_sample_size

        selected_normal = np.random.choice(normal_indices, normal_sample_size, replace=False)
        selected_attack = np.random.choice(attack_indices, attack_sample_size, replace=False)

        selected_indices = np.concatenate([selected_normal, selected_attack])
        np.random.shuffle(selected_indices)

        X_train = X_train[selected_indices]
        y_train = y_train[selected_indices]

        print(f"采样后训练集: X{X_train.shape}, y{y_train.shape}")

    # 打印标签分布
    train_normal = np.sum(y_train == 0)
    train_attack = np.sum(y_train == 1)
    test_normal = np.sum(y_test == 0)
    test_attack = np.sum(y_test == 1)

    print(f"\n训练集分布: 正常={train_normal:,} ({train_normal / len(y_train) * 100:.2f}%), "
          f"异常={train_attack:,} ({train_attack / len(y_train) * 100:.2f}%)")
    print(f"测试集分布: 正常={test_normal:,} ({test_normal / len(y_test) * 100:.2f}%), "
          f"异常={test_attack:,} ({test_attack / len(y_test) * 100:.2f}%)")

    return X_train, y_train, X_test, y_test


def train_model(X_train, y_train, X_test, y_test, data_dir):
    """训练LightGBM模型"""
    print("\n" + "=" * 60)
    print("训练LightGBM模型")
    print("=" * 60)

    # 创建数据集
    train_data = lgb.Dataset(X_train, label=y_train)
    test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

    # 参数配置
    params = {
        'objective': 'binary',
        'metric': ['auc', 'binary_logloss'],
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'is_unbalance': True,
        'random_state': 42,
        'verbose': -1
    }

    print("\n模型参数:")
    for k, v in params.items():
        print(f"  {k}: {v}")

    # 训练
    print("\n开始训练...")
    model = lgb.train(
        params,
        train_data,
        num_boost_round=1000,
        valid_sets=[train_data, test_data],
        valid_names=['train', 'test'],
        callbacks=[
            lgb.early_stopping(stopping_rounds=50),
            lgb.log_evaluation(period=50)
        ]
    )

    print(f"\n最佳迭代: {model.best_iteration}")

    # 保存模型
    model.save_model(str(data_dir / 'lightgbm_model.txt'))
    print("模型已保存")

    return model


def evaluate_model(model, X_test, y_test, data_dir):
    """评估模型"""
    print("\n" + "=" * 60)
    print("模型评估")
    print("=" * 60)

    # 预测
    y_pred_proba = model.predict(X_test)
    y_pred_binary = (y_pred_proba > 0.5).astype(int)

    # AUC
    auc_score = roc_auc_score(y_test, y_pred_proba)
    print(f"\nAUC: {auc_score:.4f}")

    # Precision-Recall AUC
    precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
    pr_auc = auc(recall, precision)
    print(f"PR-AUC: {pr_auc:.4f}")

    # 分类报告
    print("\n分类报告:")
    print(classification_report(y_test, y_pred_binary,
                                target_names=['正常', '异常'],
                                digits=4))

    # 混淆矩阵
    cm = confusion_matrix(y_test, y_pred_binary)
    print("\n混淆矩阵:")
    print(f"{'':>10} {'预测正常':>12} {'预测异常':>12}")
    print(f"{'实际正常':>10} {cm[0, 0]:>12,} {cm[0, 1]:>12,}")
    print(f"{'实际异常':>10} {cm[1, 0]:>12,} {cm[1, 1]:>12,}")

    # 计算详细指标
    tn, fp, fn, tp = cm.ravel()

    accuracy = (tp + tn) / (tp + tn + fp + fn)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0

    print(f"\n详细指标:")
    print(f"  准确率 (Accuracy): {accuracy:.4f}")
    print(f"  精确率 (Precision): {precision:.4f}")
    print(f"  召回率 (Recall): {recall:.4f}")
    print(f"  F1分数: {f1:.4f}")
    print(f"  假正率 (FPR): {fpr:.4f}")
    print(f"  假负率 (FNR): {fnr:.4f}")

    # 保存评估结果
    results = {
        'auc': float(auc_score),
        'pr_auc': float(pr_auc),
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1': float(f1),
        'fpr': float(fpr),
        'fnr': float(fnr),
        'confusion_matrix': {
            'tn': int(tn),
            'fp': int(fp),
            'fn': int(fn),
            'tp': int(tp)
        }
    }

    with open(data_dir / 'evaluation_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\n评估结果已保存到 evaluation_results.json")

    # 特征重要性
    print("\nTop 20 重要特征:")
    importance = model.feature_importance(importance_type='gain')
    feature_names = [f'feature_{i}' for i in range(len(importance))]

    feature_importance = sorted(zip(feature_names, importance),
                                key=lambda x: x[1], reverse=True)

    for i, (name, imp) in enumerate(feature_importance[:20], 1):
        print(f"  {i:2d}. {name}: {imp:.2f}")

    return results


def plot_confusion_matrix(cm, data_dir):
    """绘制混淆矩阵"""
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt=',d', cmap='Blues',
                xticklabels=['正常', '异常'],
                yticklabels=['正常', '异常'])
    plt.title('混淆矩阵')
    plt.ylabel('实际标签')
    plt.xlabel('预测标签')
    plt.tight_layout()
    plt.savefig(data_dir / 'confusion_matrix.png', dpi=300, bbox_inches='tight')
    print(f"\n混淆矩阵图已保存到 confusion_matrix.png")
    plt.close()


def main():
    data_dir = Path(__file__).parent / 'data'

    # 加载元数据
    with open(data_dir / 'split_metadata.json', 'r') as f:
        metadata = json.load(f)

    print("=" * 60)
    print("LightGBM 分层训练")
    print("=" * 60)
    print(f"测试集比例: {metadata['test_ratio']}")
    print(f"随机种子: {metadata['random_seed']}")

    # 加载数据（可选：限制训练样本数）
    # max_train_samples=1000000 表示最多使用100万训练样本
    # 设为 None 使用全部训练数据
    X_train, y_train, X_test, y_test = load_data(
        data_dir,
        max_train_samples=1000000  # 根据内存情况调整
    )

    # 训练模型
    model = train_model(X_train, y_train, X_test, y_test, data_dir)

    # 评估模型
    results = evaluate_model(model, X_test, y_test, data_dir)

    # 绘制混淆矩阵
    y_pred = (model.predict(X_test) > 0.5).astype(int)
    cm = confusion_matrix(y_test, y_pred)
    plot_confusion_matrix(cm, data_dir)

    print("\n" + "=" * 60)
    print("训练完成！")
    print("=" * 60)
    print(f"模型文件: {data_dir / 'lightgbm_model.txt'}")
    print(f"评估结果: {data_dir / 'evaluation_results.json'}")
    print(f"混淆矩阵: {data_dir / 'confusion_matrix.png'}")


if __name__ == "__main__":
    main()