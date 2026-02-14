import { useState } from 'react'
import { Form, Input, Button, Tabs, message } from 'antd'
import { Mail, Lock, User } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'
import { authApi } from '@/services/auth'
import styles from './Login.module.css'

export default function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as any)?.from?.pathname || '/'
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('login')

  const handleLogin = async (values: { email: string; password: string }) => {
    setLoading(true)
    try {
      const res: any = await authApi.login(values)
      const token = res?.access_token || res?.data?.access_token
      const refreshToken = res?.refresh_token || res?.data?.refresh_token
      if (token) {
        localStorage.setItem('token', token)
        if (refreshToken) localStorage.setItem('refresh_token', refreshToken)
        message.success('登录成功')
        navigate(from, { replace: true })
      } else {
        message.error('登录失败：未收到令牌')
      }
    } catch (e: any) {
      const raw = e?.response?.data?.detail
      const detail = Array.isArray(raw) ? raw.map((d: any) => d.msg).join('; ') : raw || '登录失败，请检查邮箱和密码'
      message.error(detail)
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (values: { username: string; email: string; password: string }) => {
    setLoading(true)
    try {
      await authApi.register(values)
      message.success('注册成功，请登录')
      setActiveTab('login')
    } catch (e: any) {
      const raw = e?.response?.data?.detail
      const detail = Array.isArray(raw) ? raw.map((d: any) => d.msg).join('; ') : raw || '注册失败'
      message.error(detail)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.card}>
        <div className={styles.brand}>
          <h1 className={styles.logo}>A股AI分析</h1>
          <p className={styles.tagline}>智能选股 · 多维分析 · AI驱动</p>
        </div>

        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          centered
          items={[
            {
              key: 'login',
              label: '登录',
              children: (
                <Form layout="vertical" onFinish={handleLogin} autoComplete="off">
                  <Form.Item name="email" rules={[{ required: true, message: '请输入邮箱' }, { type: 'email', message: '邮箱格式不正确' }]}>
                    <Input size="large" prefix={<Mail size={16} style={{ opacity: 0.4 }} />} placeholder="邮箱" />
                  </Form.Item>
                  <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
                    <Input.Password size="large" prefix={<Lock size={16} style={{ opacity: 0.4 }} />} placeholder="密码" />
                  </Form.Item>
                  <Form.Item>
                    <Button type="primary" htmlType="submit" block size="large" loading={loading}>
                      登录
                    </Button>
                  </Form.Item>
                </Form>
              ),
            },
            {
              key: 'register',
              label: '注册',
              children: (
                <Form layout="vertical" onFinish={handleRegister} autoComplete="off">
                  <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }, { min: 3, message: '至少3个字符' }]}>
                    <Input size="large" prefix={<User size={16} style={{ opacity: 0.4 }} />} placeholder="用户名" />
                  </Form.Item>
                  <Form.Item name="email" rules={[{ required: true, message: '请输入邮箱' }, { type: 'email', message: '邮箱格式不正确' }]}>
                    <Input size="large" prefix={<Mail size={16} style={{ opacity: 0.4 }} />} placeholder="邮箱" />
                  </Form.Item>
                  <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }, { min: 8, message: '至少8个字符' }]}>
                    <Input.Password size="large" prefix={<Lock size={16} style={{ opacity: 0.4 }} />} placeholder="密码" />
                  </Form.Item>
                  <Form.Item>
                    <Button type="primary" htmlType="submit" block size="large" loading={loading}>
                      注册
                    </Button>
                  </Form.Item>
                </Form>
              ),
            },
          ]}
        />

        <p className={styles.disclaimer}>
          登录即表示您同意<a onClick={() => navigate('/terms')}>用户协议</a>和<a onClick={() => navigate('/privacy')}>隐私政策</a>
        </p>
      </div>
    </div>
  )
}
