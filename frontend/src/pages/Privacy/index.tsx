import { Typography, Divider } from 'antd'
import styles from '../Disclaimer/Disclaimer.module.css'

const { Title, Paragraph } = Typography

export default function Privacy() {
  return (
    <div className={styles.container}>
      <Typography>
        <Title level={2}>隐私政策</Title>
        <Paragraph type="secondary">最后更新日期：2026年2月14日</Paragraph>
        <Divider />

        <Title level={4}>一、信息收集</Title>
        <Paragraph>
          本平台在提供服务过程中，可能收集以下类型的信息：
        </Paragraph>
        <ul className={styles.list}>
          <li><strong>账户信息：</strong>注册时提供的用户名、邮箱等</li>
          <li><strong>使用数据：</strong>您在平台上的操作记录，如搜索历史、策略偏好等</li>
          <li><strong>设备信息：</strong>浏览器类型、操作系统、IP地址等技术信息</li>
        </ul>

        <Title level={4}>二、信息使用</Title>
        <Paragraph>
          收集的信息将用于以下目的：
        </Paragraph>
        <ul className={styles.list}>
          <li>提供和改善平台服务</li>
          <li>个性化用户体验（如推荐策略）</li>
          <li>平台安全防护与异常检测</li>
          <li>服务质量分析与优化</li>
        </ul>

        <Title level={4}>三、信息存储与保护</Title>
        <Paragraph>
          我们采取合理的技术和管理措施保护您的个人信息安全，包括但不限于：
        </Paragraph>
        <ul className={styles.list}>
          <li>密码加密存储（bcrypt哈希）</li>
          <li>传输层加密（HTTPS/TLS）</li>
          <li>访问权限控制</li>
          <li>定期安全审计</li>
        </ul>

        <Title level={4}>四、信息共享</Title>
        <Paragraph>
          我们不会将您的个人信息出售、交易或转让给第三方，以下情况除外：
        </Paragraph>
        <ul className={styles.list}>
          <li>获得您的明确同意</li>
          <li>法律法规要求或政府部门依法要求</li>
          <li>为保护平台及其他用户的合法权益</li>
        </ul>

        <Title level={4}>五、Cookie 使用</Title>
        <Paragraph>
          本平台使用 Cookie 和类似技术来存储用户偏好设置（如主题选择、搜索历史）。
          这些 Cookie 仅用于改善用户体验，您可以通过浏览器设置管理 Cookie。
        </Paragraph>

        <Title level={4}>六、用户权利</Title>
        <Paragraph>
          您对个人信息享有以下权利：
        </Paragraph>
        <ul className={styles.list}>
          <li><strong>查询权：</strong>查看平台收集的个人信息</li>
          <li><strong>更正权：</strong>修改不准确的个人信息</li>
          <li><strong>删除权：</strong>要求删除个人信息</li>
          <li><strong>注销权：</strong>注销账户并删除所有相关数据</li>
        </ul>

        <Title level={4}>七、未成年人保护</Title>
        <Paragraph>
          本平台不面向未满18周岁的未成年人提供服务。
          如果我们发现收集了未成年人的个人信息，将立即删除相关数据。
        </Paragraph>

        <Title level={4}>八、政策更新</Title>
        <Paragraph>
          我们可能会不时更新本隐私政策。重大变更时，我们将在平台上发布通知。
          建议您定期查阅本页面以了解最新的隐私政策。
        </Paragraph>

        <Divider />
        <Paragraph type="secondary" style={{ textAlign: 'center' }}>
          如对本隐私政策有任何疑问，请联系平台管理员。
        </Paragraph>
      </Typography>
    </div>
  )
}
