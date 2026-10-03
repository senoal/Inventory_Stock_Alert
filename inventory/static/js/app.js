document.addEventListener('DOMContentLoaded', () => {
  const menu = document.getElementById('menuToggle');
  const sidebar = document.getElementById('sidebar');
  menu?.addEventListener('click', () => sidebar.classList.toggle('open'));
  document.addEventListener('click', (event) => {
    if (window.innerWidth < 992 && sidebar?.classList.contains('open') && !sidebar.contains(event.target) && !menu.contains(event.target)) sidebar.classList.remove('open');
  });
  const date = document.getElementById('currentDate');
  if (date) date.textContent = new Intl.DateTimeFormat('id-ID', {weekday:'long', day:'numeric', month:'long', year:'numeric'}).format(new Date());
  const movement = document.getElementById('movementType');
  movement?.addEventListener('change', () => {
    document.getElementById('quantityLabel').textContent = movement.value === 'ADJUSTMENT' ? 'Stok akhir hasil koreksi' : 'Kuantitas';
  });
});

function initDashboardCharts(data) {
  if (typeof Chart === 'undefined') return;
  Chart.defaults.font.family = "'DM Sans', sans-serif";
  Chart.defaults.color = '#7a8595';
  const movement = document.getElementById('movementChart');
  if (movement) new Chart(movement, {type:'line',data:{labels:data.trendLabels,datasets:[
    {label:'Masuk',data:data.incoming,borderColor:'#246bfd',backgroundColor:'#246bfd18',fill:true,tension:.35,borderWidth:2,pointRadius:3},
    {label:'Keluar',data:data.outgoing,borderColor:'#12a594',backgroundColor:'#12a59412',fill:true,tension:.35,borderWidth:2,pointRadius:3}
  ]},options:{maintainAspectRatio:false,plugins:{legend:{position:'top',align:'end',labels:{usePointStyle:true,boxWidth:7}}},scales:{x:{grid:{display:false}},y:{beginAtZero:true,grid:{color:'#edf0f4'}}}}});
  const category = document.getElementById('categoryChart');
  if (category) new Chart(category, {type:'doughnut',data:{labels:data.categoryLabels,datasets:[{data:data.categoryStock,backgroundColor:['#246bfd','#12a594','#8b5cf6','#f59e0b','#ef5da8','#64748b'],borderWidth:0,hoverOffset:4}]},options:{maintainAspectRatio:false,cutout:'68%',plugins:{legend:{position:'bottom',labels:{usePointStyle:true,boxWidth:7,padding:16}}}}});
}
