import React from 'react'
import { Card, Button, Table, Space, message } from 'antd'
import { DownloadOutlined, PlayCircleOutlined, PauseCircleOutlined } from '@ant-design/icons'

const ImageCapture = () => {
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id'
    },
    {
      title: '图片URL',
      dataIndex: 'url',
      key: 'url'
    },
    {
      title: '抓取时间',
      dataIndex: 'created_at',
      key: 'created_at'
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status'
    }
  ]

  return (
    <div>
      <Card
        title="图片抓取"
        extra={
          <Space>
            <Button type="primary" icon={<PlayCircleOutlined />}>
              开始抓取
            </Button>
            <Button icon={<PauseCircleOutlined />}>
              暂停抓取
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={[]}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  )
}

export default ImageCapture

