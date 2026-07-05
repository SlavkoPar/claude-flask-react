import { useEffect, useRef } from 'react'
import TomSelect from 'tom-select'
import 'tom-select/dist/css/tom-select.bootstrap5.css'
import { debounce } from '../../utils/debounce'

/**
 * Free-text search box with debounced, server-fetched suggestions (Tom Select).
 *
 * - fetchOptions(query) => Promise<Array<{ id, label }>>
 * - onSelect(option | null) fires when the user picks a suggestion
 * - requireSelection: when true, typed text that doesn't match a fetched
 *   option cannot be committed (used where a real backend id is required,
 *   e.g. picking a question in the sidebar)
 * - clearAfterSelect: reset the box to empty right after a pick, for
 *   "search then act" flows instead of "type a persistent filter" flows
 */
export default function AsyncAutocomplete({
  fetchOptions,
  onSelect,
  onInputChange,
  onResults,
  placeholder,
  requireSelection = false,
  clearAfterSelect = false,
  debounceMs = 300,
  className,
}) {
  const inputRef = useRef(null)
  const tomRef = useRef(null)
  const latestOptionsRef = useRef([])

  useEffect(() => {
    const loadOptions = debounce((query, callback) => {
      onInputChange?.(query)
      fetchOptions(query)
        .then(options => {
          latestOptionsRef.current = options
          onResults?.(options)
          callback(options)
        })
        .catch(() => callback())
    }, debounceMs)

    const ts = new TomSelect(inputRef.current, {
      valueField: 'id',
      labelField: 'label',
      searchField: 'label',
      maxItems: 1,
      persist: false,
      create: !requireSelection,
      createFilter: () => !requireSelection,
      load: loadOptions,
      shouldLoad: () => true,
      preload: true,
      onItemAdd() {
        this.blur()
      },
    })

    ts.on('item_add', value => {
      const option = latestOptionsRef.current.find(o => String(o.id) === String(value))
      onSelect?.(option || (requireSelection ? null : { id: value, label: value }))
      if (clearAfterSelect) ts.clear(true)
    })

    tomRef.current = ts
    return () => ts.destroy()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return <input ref={inputRef} type="text" placeholder={placeholder} className={className} />
}
