/**
 * A tab's panel, as its own file of code that can be fetched ahead.
 *
 * React's lazy always suspends on its first render, even when the code already
 * came in on idle or on hover: the panel area showed nothing, then React held
 * the reveal back about 300ms more. So once `preload` has the code, the panel
 * renders it directly, the same frame as the click; lazy is only the path for
 * a tab opened before its code arrived (and keeps its retry on a failed fetch).
 */
import { createElement, lazy } from 'react'

export function panel(load) {
  let Loaded = null
  const preload = () => load().then((module) => {
    Loaded = module.default
    return module
  })
  const Lazy = lazy(preload)
  const Panel = (props) => createElement(Loaded ?? Lazy, props)
  return Object.assign(Panel, { preload })
}
