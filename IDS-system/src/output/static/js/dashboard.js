function fetchDashboard() {
  fetch('/dashboard/api/chart')
    .then(r => r.json())
    .then(data => {
      // 趋势图
      const trendChart = echarts.init(document.getElementById('trend'));
      trendChart.setOption({
          tooltip: {trigger: 'axis'},
          xAxis: {type: 'category', data: data.trend.map(i => i.time)},
          yAxis: {type: 'value', name: '次数'},
          series: [{type: 'line', data: data.trend.map(i => i.count), smooth: true}]
      });

      // 饼图
      const pieChart = echarts.init(document.getElementById('pie'));
      pieChart.setOption({
          tooltip: {trigger: 'item'},
          series: [{type: 'pie', radius: '60%', data: data.pie}]
      });
    });
}

// 首次加载 + 每 30 秒刷新
fetchDashboard();
setInterval(fetchDashboard, 30_000);