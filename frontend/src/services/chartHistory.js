const KEY = 'querynova-chart-history';

const read = () => {
  try {
    return JSON.parse(localStorage.getItem(KEY) || '{"charts":[]}');
  } catch {
    return { charts: [] };
  }
};

const write = (value) => localStorage.setItem(KEY, JSON.stringify(value));

export const getChartHistory = () => read().charts || [];

export const saveChart = (chart) => {
  let state = read();
  if (state.charts.some((item) => item.id === chart.id)) return state.charts;
  state.charts = [chart, ...state.charts];
  write(state);
  return state.charts;
};

export const deleteChart = (id) => {
  let state = read();
  state.charts = state.charts.filter((item) => item.id !== id);
  write(state);
  return state.charts;
};

export const togglePinned = (id) => {
  let state = read();
  state.charts = state.charts.map((item) =>
    item.id === id ? { ...item, pinned: !item.pinned } : item
  );
  write(state);
  return state.charts;
};

export const clearChartHistory = () => {
  write({ charts: [] });
  return [];
};
