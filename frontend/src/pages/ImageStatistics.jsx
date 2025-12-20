import React from 'react'
import { Card, Row, Col } from 'antd'
import { BarChartOutlined } from '@ant-design/icons'

const ImageStatistics = () => {
  return (
    <div>
      <Card title="图片统计分析" icon={<BarChartOutlined />}>
        <Row gutter={16}>
          <Col span={24}>
            <div style={{ height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f5f5f5' }}>
              <p>统计图表区域（待实现）</p>
            </div>
          </Col>
        </Row>
      </Card>
    </div>
  )
}

export default ImageStatistics

