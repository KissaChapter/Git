import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, 
    roc_auc_score, roc_curve, precision_recall_curve, average_precision_score
)
import os
from datetime import datetime

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def validate_model():
    """LightGBM模型准确性验证 - 针对41维特征的二分类模型"""
    
    print("=" * 60)
    print("LightGBM模型验证报告")
    print("=" * 60)
    print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 加载测试数据
    test_data_path = './data/A_csv/A_00.csv'
    if not os.path.exists(test_data_path):
        raise FileNotFoundError(f"测试文件不存在: {test_data_path}")
    
    test_data = pd.read_csv(test_data_path)
    print(f"测试数据形状: {test_data.shape}")
    
    # 分离特征和标签
    X_test = test_data.iloc[:, :-1].values  # 41个特征
    y_true = test_data.iloc[:, -1].values   # 最后一列是标签
    
    # 验证特征维度
    if X_test.shape[1] != 41:
        print(f"警告: 期望41个特征，实际{X_test.shape[1]}个")
    
    # 2. 加载LightGBM模型
    model_path = './data/lightgbm_model.txt'
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"模型文件不存在: {model_path}")
    
    model = joblib.load(model_path)
    print(f"模型类型: {type(model).__name__}")
    
    # 3. 进行预测
    y_pred_proba = model.predict(X_test)
    y_pred = (y_pred_proba > 0.5).astype(int)
    
    # 4. 计算评估指标
    accuracy = accuracy_score(y_true, y_pred)
    auc_score = roc_auc_score(y_true, y_pred_proba)
    
    # 5. 类别分布分析
    unique, counts = np.unique(y_true, return_counts=True)
    class_distribution = dict(zip(unique, counts))
    
    # 6. 生成分类报告
    report = classification_report(
        y_true, y_pred, 
        target_names=['正常流量', '攻击流量'],
        output_dict=True
    )
    
    # 7. 打印结果摘要
    print("\n" + "=" * 40)
    print("验证结果摘要")
    print("=" * 40)
    print(f"测试样本总数: {len(y_true):,}")
    print(f"整体准确率: {accuracy:.2%}")
    print(f"AUC得分: {auc_score:.4f}")
    
    print("\n类别分布:")
    for label, count in class_distribution.items():
        percentage = count / len(y_true) * 100
        label_name = '攻击流量' if label == 1 else '正常流量'
        print(f"  {label_name}: {count:,} 条 ({percentage:.1f}%)")
    
    # 8. 详细分类指标
    print("\n详细分类报告:")
    print(classification_report(y_true, y_pred, target_names=['正常流量', '攻击流量']))
    
    # 9. 创建可视化图表
    create_visualizations(y_true, y_pred, y_pred_proba, model)
    
    # 10. 保存详细结果
    save_detailed_results(y_true, y_pred, y_pred_proba, report)
    
    return {
        'accuracy': accuracy,
        'auc_score': auc_score,
        'class_distribution': class_distribution,
        'classification_report': report
    }

def create_visualizations(y_true, y_pred, y_pred_proba, model):
    """创建可视化图表"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. 混淆矩阵
    cm = confusion_matrix(y_true, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['正常', '攻击'], yticklabels=['正常', '攻击'],
                ax=axes[0,0])
    axes[0,0].set_title('混淆矩阵')
    axes[0,0].set_ylabel('真实标签')
    axes[0,0].set_xlabel('预测标签')
    
    # 2. ROC曲线
    fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
    axes[0,1].plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC曲线 (AUC = {roc_auc_score(y_true, y_pred_proba):.3f})')
    axes[0,1].plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    axes[0,1].set_xlim([0.0, 1.0])
    axes[0,1].set_ylim([0.0, 1.05])
    axes[0,1].set_xlabel('假正率')
    axes[0,1].set_ylabel('真正率')
    axes[0,1].set_title('ROC曲线')
    axes[0,1].legend(loc="lower right")
    
    # 3. 精确率-召回率曲线
    precision, recall, _ = precision_recall_curve(y_true, y_pred_proba)
    ap_score = average_precision_score(y_true, y_pred_proba)
    axes[1,0].plot(recall, precision, color='blue', lw=2, label=f'PR曲线 (AP = {ap_score:.3f})')
    axes[1,0].set_xlabel('召回率')
    axes[1,0].set_ylabel('精确率')
    axes[1,0].set_title('精确率-召回率曲线')
    axes[1,0].legend(loc="lower left")
    
    # 4. 特征重要性（前20个）
    try:
        feature_importance = model.feature_importances_
        feature_names = [f'Column_{i}' for i in range(len(feature_importance))]
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': feature_importance
        }).sort_values('importance', ascending=False).head(20)
        
        axes[1,1].barh(range(len(importance_df)), importance_df['importance'])
        axes[1,1].set_yticks(range(len(importance_df)))
        axes[1,1].set_yticklabels(importance_df['feature'])
        axes[1,1].set_xlabel('重要性得分')
        axes[1,1].set_title('特征重要性（前20个）')
        axes[1,1].invert_yaxis()
    except:
        axes[1,1].text(0.5, 0.5, '无法获取特征重要性', ha='center', va='center')
    
    plt.tight_layout()
    plt.savefig('./output/model_validation_charts.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("\n可视化图表已保存至: ./output/model_validation_charts.png")

def save_detailed_results(y_true, y_pred, y_pred_proba, report):
    """保存详细验证结果"""
    # 创建结果DataFrame
    results_df = pd.DataFrame({
        '真实标签': y_true,
        '预测标签': y_pred,
        '预测概率': y_pred_proba,
        '是否正确': y_true == y_pred
    })
    
    # 保存详细结果
    results_df.to_csv('./output/validation_detailed_results.csv', index=False)
    
    # 保存分类报告
    report_df = pd.DataFrame(report).T
    report_df.to_csv('./output/validation_classification_report.csv')
    
    # 保存汇总信息
    summary = {
        '验证时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '测试样本数': len(y_true),
        '整体准确率': accuracy_score(y_true, y_pred),
        'AUC得分': roc_auc_score(y_true, y_pred_proba),
        '类别分布': dict(zip(*np.unique(y_true, return_counts=True))),
        '模型信息': 'LightGBM二分类模型，41个特征'
    }
    
    with open('./output/validation_summary.json', 'w', encoding='utf-8') as f:
        import json
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print("\n详细结果已保存:")
    print("- 详细结果: ./output/validation_detailed_results.csv")
    print("- 分类报告: ./output/validation_classification_report.csv")
    print("- 汇总信息: ./output/validation_summary.json")

if __name__ == "__main__":
    # 确保输出目录存在
    os.makedirs('./output', exist_ok=True)
    
    try:
        results = validate_model()
        print("\n" + "=" * 60)
        print("验证完成！")
        print("=" * 60)
    except Exception as e:
        print(f"\n验证过程中出现错误: {str(e)}")
        print("请检查:")
        print("1. 测试数据文件是否存在: ./data/A_csv/A_00.csv")
        print("2. 模型文件是否存在: ./models/data/lightgbm_model.txt")
        print("3. 特征维度是否匹配（应为41维）")