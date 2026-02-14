import { Alert } from 'antd'
import { AlertTriangle } from 'lucide-react'

interface RiskDisclaimerProps {
  compact?: boolean
}

export default function RiskDisclaimer({ compact = false }: RiskDisclaimerProps) {
  if (compact) {
    return (
      <div style={{
        padding: '8px 12px',
        background: 'rgba(255,165,0,0.06)',
        borderRadius: 6,
        border: '1px solid rgba(255,165,0,0.15)',
        fontSize: 12,
        opacity: 0.8,
        display: 'flex',
        alignItems: 'flex-start',
        gap: 6,
      }}>
        <AlertTriangle size={14} style={{ marginTop: 1, flexShrink: 0, color: '#faad14' }} />
        <span>
          本平台提供的所有分析结果仅供参考，不构成投资建议。股市有风险，投资需谨慎。
        </span>
      </div>
    )
  }

  return (
    <Alert
      type="warning"
      showIcon
      icon={<AlertTriangle size={20} />}
      message="投资风险提示"
      description={
        <div style={{ fontSize: 13, lineHeight: 1.8 }}>
          <p style={{ marginBottom: 8 }}>
            <strong>重要声明：</strong>本平台（A股AI智能分析系统）提供的所有数据、分析报告、选股结果和投资建议仅供参考，
            不构成任何形式的投资建议或投资承诺。
          </p>
          <ul style={{ paddingLeft: 20, margin: 0 }}>
            <li>本平台数据来源于公开市场信息，不保证数据的完整性、准确性和及时性。</li>
            <li>历史数据和模型分析不代表未来表现，过往业绩不预示未来收益。</li>
            <li>股票投资具有较高风险，可能导致本金损失，请根据自身风险承受能力谨慎决策。</li>
            <li>本平台不对因使用本平台信息而产生的任何直接或间接损失承担责任。</li>
            <li>投资者应当独立判断，自主决策，自行承担投资风险。</li>
          </ul>
          <p style={{ marginTop: 8, marginBottom: 0, opacity: 0.7 }}>
            根据《中华人民共和国证券法》等相关法律法规，本平台不从事证券投资咨询业务，
            不提供个性化投资咨询服务。如需专业投资建议，请咨询持牌证券投资顾问。
          </p>
        </div>
      }
      style={{ marginBottom: 16 }}
    />
  )
}
