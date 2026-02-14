import api from './api'

export interface LoginParams {
  email: string
  password: string
}

export interface RegisterParams {
  username: string
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface UserResponse {
  id: number
  username: string
  email: string
  created_at: string
}

export const authApi = {
  login: (params: LoginParams): Promise<TokenResponse> =>
    api.post('/auth/login', params),

  register: (params: RegisterParams): Promise<UserResponse> =>
    api.post('/auth/register', params),

  logout: (): Promise<void> =>
    api.post('/auth/logout'),
}
