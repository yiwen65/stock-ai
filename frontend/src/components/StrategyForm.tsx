import { Form, Select, InputNumber, Button, Input } from 'antd'
import { Search } from 'lucide-react'
import styles from './StrategyForm.module.css'

interface StrategyFormProps {
  onSubmit: (values: any) => void
  loading?: boolean
}

export default function StrategyForm({ onSubmit, loading }: StrategyFormProps) {
  const [form] = Form.useForm()

  return (
    <div className={styles.formContainer}>
      <Form
        form={form}
        onFinish={onSubmit}
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
            <Select size="large" className={styles.select}>
              <Select.Option value="graham">格雷厄姆价值投资</Select.Option>
              <Select.Option value="buffett">巴菲特护城河</Select.Option>
              <Select.Option value="peg">PEG成长策略</Select.Option>
              <Select.Option value="custom">自定义策略</Select.Option>
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
      </Form>
    </div>
  )
}
