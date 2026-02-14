import { Typography, Divider } from 'antd'
import styles from '../Disclaimer/Disclaimer.module.css'

const { Title, Paragraph, Text } = Typography

export default function Terms() {
  return (
    <div className={styles.container}>
      <Typography>
        <Title level={2}>用户协议</Title>
        <Paragraph type="secondary">最后更新日期：2026年2月14日</Paragraph>
        <Divider />

        <Title level={4}>一、服务条款接受</Title>
        <Paragraph>
          欢迎使用A股AI智能分析平台（以下简称"本平台"）。使用本平台的服务即表示您同意
          遵守以下用户协议条款。如果您不同意任何条款，请停止使用本平台。
        </Paragraph>

        <Title level={4}>二、服务描述</Title>
        <Paragraph>
          本平台提供基于人工智能技术的A股市场数据分析、选股策略筛选和投资研究辅助工具。
          具体服务包括但不限于：
        </Paragraph>
        <ul className={styles.list}>
          <li>股票基本面、技术面、资金面的多维度分析</li>
          <li>经典投资策略和自定义策略的选股筛选</li>
          <li>自然语言策略描述的智能解析</li>
          <li>市场行情数据展示</li>
        </ul>

        <Title level={4}>三、用户行为规范</Title>
        <Paragraph>
          在使用本平台服务时，您同意：
        </Paragraph>
        <ul className={styles.list}>
          <li>不利用本平台进行任何违法违规活动</li>
          <li>不对本平台进行反向工程、破解或未授权访问</li>
          <li>不通过自动化手段大量抓取平台数据</li>
          <li>不将本平台的分析结果作为唯一投资决策依据</li>
          <li>不以任何方式干扰平台正常运行</li>
        </ul>

        <Title level={4}>四、信息准确性</Title>
        <Paragraph>
          本平台尽力确保所提供信息的准确性和及时性，但不对以下情况做出保证：
        </Paragraph>
        <ul className={styles.list}>
          <li>数据的绝对准确性和完整性</li>
          <li>AI分析结果的正确性</li>
          <li>服务的不间断运行</li>
          <li>分析模型的预测准确率</li>
        </ul>

        <Title level={4}>五、知识产权</Title>
        <Paragraph>
          本平台的所有内容、算法、设计和代码均受知识产权法律保护。
          未经书面授权，用户不得复制、修改、传播或用于商业用途。
          用户在平台上创建的个人策略归用户所有。
        </Paragraph>

        <Title level={4}>六、免责条款</Title>
        <Paragraph>
          <Text type="danger" strong>
            本平台提供的所有信息和分析结果仅供参考，不构成投资建议。
            用户因使用本平台信息做出的投资决策及其产生的任何损失，
            本平台不承担任何责任。
          </Text>
        </Paragraph>

        <Title level={4}>七、服务变更与终止</Title>
        <Paragraph>
          本平台保留在任何时候修改或终止服务的权利，恕不另行通知。
          本平台有权根据实际情况修改本用户协议的条款。
          修改后的条款一经发布即生效。
        </Paragraph>

        <Title level={4}>八、适用法律</Title>
        <Paragraph>
          本协议的签订、履行、解释及争议解决均适用中华人民共和国法律。
          因本协议引发的争议，双方应首先协商解决。
        </Paragraph>

        <Divider />
        <Paragraph type="secondary" style={{ textAlign: 'center' }}>
          继续使用本平台即表示您已阅读并同意以上用户协议。
        </Paragraph>
      </Typography>
    </div>
  )
}
