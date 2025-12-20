import React from 'react'
import { Card, Row, Col, Statistic } from 'antd'
import { PictureOutlined, TagsOutlined, DownloadOutlined } from '@ant-design/icons'

const Dashboard = () => {
  return (
    <div>
      <h1>仪表盘</h1>
      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="总图片数"
              value={0}
              prefix={<PictureOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="已打标图片"
              value={0}
              prefix={<TagsOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="今日抓取"
              value={0}
              prefix={<DownloadOutlined />}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard

