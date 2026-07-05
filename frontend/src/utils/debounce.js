export function debounce(fn, delayMs) {
  let timeout
  return (...args) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => fn(...args), delayMs)
  }
}
