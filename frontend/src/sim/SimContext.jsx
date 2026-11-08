import { createContext, useContext } from 'react'

export const SimContext = createContext(null)

export function useSim() {
  return useContext(SimContext)
}
