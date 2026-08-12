import { createContext, useContext, useState } from 'react'
import api from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem('climate-ai-user')
    return raw ? JSON.parse(raw) : null
  })

  const login = async (username, password) => {
    const { data } = await api.post('/auth/login', { username, password })
    const sessionUser = { username: data.username, role: data.role, token: data.token }
    localStorage.setItem('climate-ai-user', JSON.stringify(sessionUser))
    setUser(sessionUser)
    return sessionUser
  }

  const logout = () => {
    localStorage.removeItem('climate-ai-user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
