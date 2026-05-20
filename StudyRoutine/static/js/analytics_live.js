/**
 * Обновление аналитики и счётчиков на дашборде при смене статуса задач / pomodoro.
 */
(function () {
  'use strict';

  let taskChart = null;
  let topicChart = null;

  function getCsrf() {
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    if (input) return input.value;
    const board = document.getElementById('kanban-board');
    if (board && board.dataset.csrf) return board.dataset.csrf;
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function updateWeekBars(weekData) {
    const container = document.getElementById('analytics-week');
    if (!container || !weekData) return;
    const cols = container.querySelectorAll('.week-bar-col');
    weekData.forEach(function (day, i) {
      const col = cols[i];
      if (!col) return;
      const minsLabel = col.querySelector('[data-week-minutes]');
      const minsFill = col.querySelector('[data-week-minutes-fill]');
      const tasksLabel = col.querySelector('[data-week-tasks]');
      const tasksFill = col.querySelector('[data-week-tasks-fill]');
      if (minsLabel) minsLabel.textContent = day.minutes + 'м';
      if (minsFill) minsFill.style.height = day.height_pct + '%';
      if (tasksLabel) {
        tasksLabel.textContent = day.tasks_done + '/' + day.tasks_total;
      }
      if (tasksFill) tasksFill.style.height = day.tasks_height_pct + '%';
    });
  }

  function updateExamStats(examStats) {
    const container = document.getElementById('analytics-exams');
    if (!container || !examStats) return;
    container.innerHTML = '';
    if (!examStats.length) {
      container.innerHTML = '<p class="empty-state">Нет данных о сессиях.</p>';
      return;
    }
    examStats.forEach(function (item) {
      const wrap = document.createElement('div');
      wrap.style.marginBottom = '14px';
      wrap.innerHTML =
        '<div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:5px;">' +
        '<span>' + escapeHtml(item.title) + '</span>' +
        '<span style="color:var(--lime);">' + item.minutes + ' мин</span></div>' +
        '<div class="progress-bar-wrap"><div class="progress-bar-fill" style="width:' +
        item.width_pct +
        '%;"></div></div>';
      container.appendChild(wrap);
    });
  }

  function escapeHtml(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
  }

  function updateCharts(data) {
    if (typeof Chart === 'undefined') return;
    const taskCtx = document.getElementById('tasks-chart');
    if (taskCtx) {
      if (taskChart) {
        taskChart.data.labels = data.task_chart_labels;
        taskChart.data.datasets[0].data = data.task_chart_data;
        taskChart.update();
      }
    }
    const topicCtx = document.getElementById('topics-chart');
    if (topicCtx) {
      if (topicChart) {
        topicChart.data.labels = data.topic_chart_labels;
        topicChart.data.datasets[0].data = data.topic_chart_data;
        topicChart.update();
      }
    }
  }

  function applyPayload(data) {
    setText('stat-total-minutes', data.total_minutes);
    setText('stat-total-sessions', data.total_sessions);
    setText('stat-done-topics', data.done_topics);
    setText('stat-total-topics', data.total_topics);
    setText('stat-minutes-today', data.minutes_today);
    setText('stat-tasks-today', data.tasks_total);
    setText('stat-tasks-done-sub', data.tasks_done + ' выполнено');
    setText('stat-tasks-pct', data.tasks_pct);

    const progressFill = document.getElementById('stat-tasks-progress');
    if (progressFill) progressFill.style.width = data.tasks_pct + '%';

    const dashDone = document.getElementById('dashboard-tasks-done');
    if (dashDone) dashDone.textContent = data.tasks_done + ' выполнено';

    updateWeekBars(data.week_data);
    updateExamStats(data.exam_stats);
    updateCharts(data);
  }

  function refreshAnalytics() {
    const root = document.querySelector('[data-analytics-url]');
    const url = root ? root.dataset.analyticsUrl : null;
    if (!url) return Promise.resolve();
    return fetch(url, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin',
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        if (data.ok) applyPayload(data);
      })
      .catch(function () {});
  }

  window.StudyRoutineRefreshStats = refreshAnalytics;

  window.addEventListener('studyroutine:stats-changed', refreshAnalytics);

  document.addEventListener('submit', function (e) {
    const form = e.target;
    if (form && form.action && form.action.indexOf('session/add') !== -1) {
      setTimeout(refreshAnalytics, 500);
    }
  });

  window.StudyRoutineBindCharts = function (taskChartInstance, topicChartInstance) {
    taskChart = taskChartInstance;
    topicChart = topicChartInstance;
  };
})();
