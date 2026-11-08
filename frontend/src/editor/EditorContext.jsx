import { createContext, useContext } from 'react'

export const EditorContext = createContext(null)

export function useEditor() {
  return useContext(EditorContext)
}