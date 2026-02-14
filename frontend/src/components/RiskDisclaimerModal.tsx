import { useState, useEffect } from 'react'
import { Modal, Checkbox } from 'antd'
import { AlertTriangle } from 'lucide-react'

const STORAGE_KEY = 'risk_disclaimer_accepted'

export default function RiskDisclaimerModal() {
  const [open, setOpen] = useState(false)
  const [checked, setChecked] = useState(false)

  useEffect(() => {
    const accepted = localStorage.getItem(STORAGE_KEY)
    if (!accepted) setOpen(true)
  }, [])

  const handleOk = () => {
    if (!checked) return
    localStorage.setItem(STORAGE_KEY, Date.now().toString())
    setOpen(false)
  }

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#faad14' }}>
          <AlertTriangle size={22} />
          <span style={{ fontSize: 18, fontWeight: 700 }}>重要风险提示</span>
        </div>
      }
      open={open}
      closable={false}
      maskClosable={false}
      keyboard={false}
      okText="同意并继续"
      cancelButtonProps={{ style: { display: 'none' } }}
      okButtonProps={{ disabled: !checked, type: 'primary' }}
      onOk={handleOk}
      width={560}
      styles={{
        body: { maxHeight: '60vh', overflowY: 'auto' },
        mask: { backdropFilter: 'blur(4px)' },
      }}
    >
      <div style={{ fontSize: 14, lineHeight: 2, color: 'rgba(255,255,255,0.85)' }}>
        <p>
          <strong>1.</strong> 本应用提供的所有分析、评分、建议仅供参考，不构成任何投资建议。
        </p>
        <p>
          <strong>2.</strong> 股市有风险，投资需谨慎。历史数据和AI分析不能保证未来收益。
        </p>
        <p>
          <strong>3.</strong> 用户应根据自身风险承受能力、投资目标和财务状况独立做出投资决策。
        </p>
        <p>
          <strong>4.</strong> 本应用不对用户的投资损失承担任何责任。
        </p>
        <p>
          <strong>5.</strong> 用户在使用本应用进行投资决策前，应咨询专业的投资顾问。
        </p>
        <p>
          <strong>6.</strong> 本应用的数据来源于第三方，我们尽力确保数据准确性，但不保证数据的完整性、准确性和及时性。
        </p>
        <p>
          <strong>7.</strong> AI分析结果基于历史数据和统计模型，存在局限性，可能出现误判。
        </p>
        <p>
          <strong>8.</strong> 市场环境、政策变化、突发事件等因素可能导致分析结果失效。
        </p>
      </div>
      <div style={{ marginTop: 16, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.1)' }}>
        <Checkbox checked={checked} onChange={(e) => setChecked(e.target.checked)}>
          <span style={{ fontWeight: 600 }}>我已阅读并理解上述风险提示</span>
        </Checkbox>
      </div>
    </Modal>
  )
}
