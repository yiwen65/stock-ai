import { Typography, Divider, Card } from 'antd'
import styles from './Disclaimer.module.css'

const { Title, Paragraph, Text } = Typography

export default function Disclaimer() {
  return (
    <div className={styles.container}>
      <Typography>
        <Title level={2}>免责声明</Title>
        <Paragraph type="secondary">最后更新日期：2026年2月14日</Paragraph>
        <Divider />

        <Title level={4}>一、服务性质说明</Title>
        <Paragraph>
          本平台（以下简称"平台"）提供的所有股票分析、选股策略、投资评分及相关信息，
          均为基于公开市场数据和算法模型生成的<Text strong>参考性信息</Text>，
          <Text type="danger" strong>不构成任何投资建议、投资推荐或投资决策依据</Text>。
        </Paragraph>

        <Title level={4}>二、数据来源与准确性</Title>
        <Paragraph>
          本平台数据来源于公开市场信息（包括但不限于交易所公开数据、上市公司公告等），
          虽然我们尽力确保数据的准确性和及时性，但不对数据的完整性、准确性、及时性做出任何保证。
          数据可能存在延迟、遗漏或错误。
        </Paragraph>

        <Title level={4}>三、AI 分析局限性</Title>
        <Paragraph>
          本平台使用人工智能技术进行股票分析，AI 分析结果存在以下局限性：
        </Paragraph>
        <ul className={styles.list}>
          <li>AI 模型基于历史数据训练，无法预测突发事件对市场的影响</li>
          <li>技术指标分析基于统计概率，不代表未来走势的确定性判断</li>
          <li>基本面分析依赖财务报表数据，可能无法反映公司最新经营状况</li>
          <li>资金面分析存在数据延迟，不代表实时资金动向</li>
          <li>综合评分为量化模型输出，仅供参考</li>
        </ul>

        <Title level={4}>四、投资风险提示</Title>
        <Card className={styles.riskCard}>
          <Paragraph>
            <Text type="danger" strong>
              股市有风险，投资需谨慎。过往业绩不代表未来表现。
            </Text>
          </Paragraph>
          <Paragraph>
            用户在做出任何投资决策前，应当：
          </Paragraph>
          <ul className={styles.list}>
            <li>充分了解相关投资产品的风险特征</li>
            <li>根据自身的风险承受能力和投资目标做出独立判断</li>
            <li>必要时咨询专业的持牌投资顾问</li>
            <li>不应将本平台信息作为唯一的决策依据</li>
          </ul>
        </Card>

        <Title level={4}>五、责任限制</Title>
        <Paragraph>
          在法律允许的最大范围内，本平台及其运营方不对以下情况承担任何责任：
        </Paragraph>
        <ul className={styles.list}>
          <li>用户基于本平台信息做出的投资决策所导致的任何损失</li>
          <li>因数据延迟、错误或遗漏导致的任何损失</li>
          <li>因系统故障、网络中断等技术原因导致的服务中断</li>
          <li>因不可抗力事件导致的任何损失</li>
        </ul>

        <Title level={4}>六、知识产权</Title>
        <Paragraph>
          本平台的所有内容（包括但不限于分析算法、界面设计、文字内容）均受知识产权法律保护。
          未经授权，不得复制、传播或用于商业用途。
        </Paragraph>

        <Title level={4}>七、资质声明</Title>
        <Paragraph>
          本平台为信息技术服务平台，不具备证券投资咨询业务资格，
          不从事证券经纪、资产管理等金融业务。平台提供的分析工具仅供个人学习和研究使用。
        </Paragraph>

        <Divider />
        <Paragraph type="secondary" style={{ textAlign: 'center' }}>
          使用本平台即表示您已阅读并同意以上免责声明。
          如有疑问，请联系平台管理员。
        </Paragraph>
      </Typography>
    </div>
  )
}
