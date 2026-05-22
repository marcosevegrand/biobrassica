(function () {
  function collectState(root) {
    const state = {}
    root.querySelectorAll('input[type="checkbox"][data-day][data-slot]').forEach((checkbox) => {
      const day = checkbox.dataset.day
      const slot = checkbox.dataset.slot
      if (!state[day]) {
        state[day] = []
      }
      if (checkbox.checked) {
        state[day].push(slot)
      }
    })
    return state
  }

  function syncHiddenInput(root) {
    const inputId = root.dataset.inputId
    const hiddenInput = document.getElementById(inputId)
    if (!hiddenInput) {
      return
    }
    hiddenInput.value = JSON.stringify(collectState(root))
  }

  function clearDay(root, day) {
    root.querySelectorAll('input[type="checkbox"][data-day="' + day + '"]').forEach((checkbox) => {
      checkbox.checked = false
    })
    syncHiddenInput(root)
  }

  function initPickupSchedule(root) {
    if (root.dataset.initialized === 'true') {
      return
    }
    root.dataset.initialized = 'true'

    root.querySelectorAll('input[type="checkbox"][data-day][data-slot]').forEach((checkbox) => {
      checkbox.addEventListener('change', function () {
        syncHiddenInput(root)
      })
    })

    root.querySelectorAll('[data-clear-day]').forEach((button) => {
      button.addEventListener('click', function () {
        clearDay(root, button.dataset.clearDay)
      })
    })

    const clearWeekButton = root.querySelector('[data-clear-week]')
    if (clearWeekButton) {
      clearWeekButton.addEventListener('click', function () {
        root.querySelectorAll('input[type="checkbox"][data-day][data-slot]').forEach((checkbox) => {
          checkbox.checked = false
        })
        syncHiddenInput(root)
      })
    }

    syncHiddenInput(root)
  }

  function initAllPickupSchedules() {
    document.querySelectorAll('[data-pickup-schedule]').forEach(initPickupSchedule)
  }

  document.addEventListener('DOMContentLoaded', initAllPickupSchedules)
  document.addEventListener('htmx:afterSwap', initAllPickupSchedules)
})()
