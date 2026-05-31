let chartCantidad, chartLeadTime, chartStock;

function chartDay(record) {
  return record.dia_mes ?? record.dia_semana ?? record.id;
}

function cargarDatos() {
  const select = document.getElementById('cargaFiltro');
  const id_carga = select.value;
  const fecha = select.options[select.selectedIndex].dataset.fecha;

  if (!id_carga || !fecha) {
    alert('Seleccione una carga válida.');
    return;
  }

  fetch(`/dashboard/data/?id_carga=${encodeURIComponent(id_carga)}&fecha=${encodeURIComponent(fecha)}`)
    .then(async (response) => {
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        alert(data.error || 'No se pudieron cargar los datos.');
        return;
      }
      if (data.error) {
        alert(data.error);
        return;
      }
      if (!data.data || data.data.length === 0) {
        alert('No hay registros para esta carga.');
        return;
      }
      mostrarGraficos(data.data, data.producto, data.mes);
    })
    .catch(() => alert('Error de conexión al cargar el dashboard.'));
}

function mostrarGraficos(data, producto, mes) {
  data.sort((a, b) => chartDay(a) - chartDay(b));

  const dias = data.map(chartDay);
  const cantidad = data.map(d => d.cantidad_unitaria);
  const leadTime = data.map(d => d.lead_time_dias);
  const stock = data.map(d => d.stock_almacen);

  if (chartCantidad) chartCantidad.destroy();
  if (chartLeadTime) chartLeadTime.destroy();
  if (chartStock) chartStock.destroy();

  const ctxCantidad = document.getElementById('graficoCantidadUnitaria').getContext('2d');
  chartCantidad = new Chart(ctxCantidad, {
    type: 'line',
    data: {
      labels: dias,
      datasets: [{
        label: 'Cantidad Unitaria',
        data: cantidad,
        fill: true,
        borderColor: '#1E3A8A',
        backgroundColor: 'rgba(30, 58, 138, 0.1)',
        tension: 0.2
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: `Variación de Cantidad Unitaria - ${producto} (Mes: ${mes})`,
          font: { size: 18 }
        }
      },
      scales: {
        x: { title: { display: true, text: 'Día del Mes' } },
        y: { title: { display: true, text: 'Cantidad Unitaria' } }
      }
    }
  });

  const ctxLeadTime = document.getElementById('graficoLeadTimeDias').getContext('2d');
  chartLeadTime = new Chart(ctxLeadTime, {
    type: 'line',
    data: {
      labels: dias,
      datasets: [{
        label: 'Lead Time (días)',
        data: leadTime,
        fill: true,
        borderColor: '#15803D',
        backgroundColor: 'rgba(21, 128, 61, 0.1)',
        tension: 0.2
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: `Lead Time (días) - ${producto} (Mes: ${mes})`,
          font: { size: 18 }
        }
      },
      scales: {
        x: { title: { display: true, text: 'Día del Mes' } },
        y: { title: { display: true, text: 'Lead Time (días)' } }
      }
    }
  });

  const ctxStock = document.getElementById('graficoStockAlmacen').getContext('2d');
  chartStock = new Chart(ctxStock, {
    type: 'line',
    data: {
      labels: dias,
      datasets: [{
        label: 'Stock en Almacén',
        data: stock,
        fill: true,
        borderColor: '#B91C1C',
        backgroundColor: 'rgba(185, 28, 28, 0.1)',
        tension: 0.2
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: `Stock en Almacén - ${producto} (Mes: ${mes})`,
          font: { size: 18 }
        }
      },
      scales: {
        x: { title: { display: true, text: 'Día del Mes' } },
        y: { title: { display: true, text: 'Stock en Almacén' } }
      }
    }
  });
}

function descargarDatos() {
  const select = document.getElementById('cargaFiltro');
  const id_carga = select.value;
  const fecha = select.options[select.selectedIndex].dataset.fecha;

  if (!id_carga || !fecha) {
    alert('Seleccione una carga válida.');
    return;
  }

  const url = `/dashboard/pdf/?id_carga=${encodeURIComponent(id_carga)}&fecha=${encodeURIComponent(fecha)}`;
  window.open(url, '_blank');
}
