/**
 * The hidden file chooser behind a button: PictureButton's photo, the Reader's PDF.
 * `pick` is a ref the button calls (`pick.current()`); `onPicked` gets the File.
 */
import { useImperativeHandle, useRef } from 'react'

export default function FilePick({ pick, accept, onPicked }) {
  const input = useRef(null)
  useImperativeHandle(pick, () => () => input.current?.click())
  return (
    <input
      ref={input}
      type="file"
      accept={accept}
      hidden
      onChange={(event) => {
        const file = event.target.files?.[0]
        event.target.value = '' // the same file chosen twice is still a choice
        if (file) onPicked(file)
      }}
    />
  )
}
