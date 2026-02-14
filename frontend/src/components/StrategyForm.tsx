import { useState } from 'react'
import { Form, Select, InputNumber, Button, Input, Typography, Tag } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { strategyApi } from '@/services/strategy'
import styles from './StrategyForm.module.css'

const { Text } = Typography
const { TextArea } = Input

const STRATEGIES = [
  { value: 'graham', label: '格雷厄姆价值投资', category: '价值', color: 'blue', desc: 'PE<15, PB<2, 低负债, 高流动比率' },
  { value: 'buffett', label: '巴菲特护城河', category: '价值', color: 'blue', desc: 'ROE>15%, 低负债, 盈利稳定, 大盘蓝筹' },
  { value: 'peg', label: 'PEG成长策略', category: '成长', color: 'green', desc: 'PEG<1, 净利润增长>20%, ROE>10%' },
  { value: 'lynch', label: '彼得·林奇成长', category: '成长', color: 'green', desc: 'PE<20, 营收增长>15%, 净利润增长>15%' },
  { value: 'ma_breakout', label: '均线多头排列', category: '技术', color: 'orange', desc: 'MA5>MA10>MA20>MA60, 放量确认' },
  { value: 'macd_divergence', label: 'MACD底背离', category: '技术', color: 'orange', desc: '价格新低但MACD不创新低, RSI超卖' },
  { value: 'volume_breakout', label: '放量突破平台', category: '技术', color: 'orange', desc: '横盘整理后放量突破前高' },
  { value: 'earnings_surprise', label: '业绩预增驱动', category: '事件', color: 'purple', desc: '净利润增长>30%, PE合理' },
  { value: 'northbound', label: '北向资金流入', category: '资金', color: 'red', desc: '主力资金持续净流入, 大盘蓝筹' },
  { value: 'rs_momentum', label: 'RS相对强度动量', category: '技术', color: 'orange', desc: '60日涨幅领先, 量价配合, 趋势延续' },
  { value: 'dual_momentum', label: '双动量策略', category: '技术', color: 'orange', desc: '绝对动量+相对动量, 回撤控制, 跑赢沪深300' },
  { value: 'quality_factor', label: '质量因子策略', category: '价值', color: 'blue', desc: 'ROE>12%, 低负债, 高毛利, 盈利稳定' },
  { value: 'shareholder_increase', label: '股东增持/回购', category: '事件', color: 'purple', desc: '机构增持信号, 低位增持, 基本面过滤' },
  { value: 'custom', label: '自定义策略', category: '自定义', color: 'default', desc: '用自然语言描述你的选股条件' },
]

interface StrategyFormProps {
  onSubmit: (values: any) => void
  loading?: boolean
}

export default function StrategyForm({ onSubmit, loading }: StrategyFormProps) {
  const [form] = Form.useForm()
  const [selectedStrategy, setSelectedStrategy] = useState('graham')
  const strategyInfo = STRATEGIES.find(s => s.value === selectedStrategy)

  const { data: industriesRaw } = useQuery({
    queryKey: ['industries'],
    queryFn: () => strategyApi.listIndustries(),
    staleTime: 600000,
  })
  const industries: string[] = Array.isArray(industriesRaw) ? industriesRaw : (industriesRaw as any)?.data || []

  const handleSubmit = (values: any) => {
    const payload: any = { ...values }
    if (values.strategy_type === 'custom' && values.custom_description) {
      payload.conditions = { description: values.custom_description }
    }
    if (values.include_industries?.length) {
      payload.include_industries = values.include_industries
    }
    if (values.exclude_industries?.length) {
      payload.exclude_industries = values.exclude_industries
    }
    onSubmit(payload)
  }

  return (
    <div className={styles.formContainer}>
      <Form
        form={form}
        onFinish={handleSubmit}
        layout="vertical"
        className={styles.form}
      >
        <div className={styles.formGrid}>
          <Form.Item
            name="strategy_type"
            label="策略类型"
            initialValue="graham"
            rules={[{ required: true, message: '请选择策略类型' }]}
          >
            <Select
              size="large"
              className={styles.select}
              onChange={(val) => setSelectedStrategy(val)}
            >
              {STRATEGIES.map(s => (
                <Select.Option key={s.value} value={s.value}>
                  <Tag color={s.color} style={{ marginRight: 6 }}>{s.category}</Tag>
                  {s.label}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="limit"
            label="结果数量"
            initialValue={50}
          >
            <InputNumber
              min={10}
              max={100}
              size="large"
              className={styles.input}
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Form.Item className={styles.submitWrapper}>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              loading={loading}
              className={styles.submitButton}
              icon={<Search size={18} />}
            >
              执行选股
            </Button>
          </Form.Item>
        </div>

        {industries.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 12 }}>
            <Form.Item name="include_industries" label="限定行业（可选）">
              <Select
                mode="multiple"
                allowClear
                placeholder="仅筛选这些行业"
                maxTagCount={3}
                options={industries.map(i => ({ label: i, value: i }))}
              />
            </Form.Item>
            <Form.Item name="exclude_industries" label="排除行业（可选）">
              <Select
                mode="multiple"
                allowClear
                placeholder="排除这些行业"
                maxTagCount={3}
                options={industries.map(i => ({ label: i, value: i }))}
              />
            </Form.Item>
          </div>
        )}

        {strategyInfo && (
          <div style={{ marginTop: 8, opacity: 0.7 }}>
            <Text type="secondary">策略说明：{strategyInfo.desc}</Text>
          </div>
        )}

        {selectedStrategy === 'custom' && (
          <Form.Item
            name="custom_description"
            label="策略描述"
            style={{ marginTop: 16 }}
            rules={[{ required: selectedStrategy === 'custom', message: '请输入策略描述' }]}
          >
            <TextArea
              rows={3}
              placeholder="用自然语言描述你的选股条件，例如：找出市盈率低于15，ROE大于15%，资产负债率低于50%的大盘蓝筹股"
              size="large"
            />
          </Form.Item>
        )}
      </Form>
    </div>
  )
}
