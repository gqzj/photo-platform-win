import React from 'react'
import { Card, Button, Table, Space, Tag } from 'antd'
import { TagsOutlined, EditOutlined } from '@ant-design/icons'

const ImageTagging = () => {
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id'
    },
    {
      title: '图片预览',
      dataIndex: 'thumbnail',
      key: 'thumbnail',
      render: (text) => <img src={text} alt="预览" style={{ width: 100, height: 100, objectFit: 'cover' }} />
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags) => (
        <Space>
          {tags?.map((tag, index) => (
            <Tag key={index} color="blue">{tag}</Tag>
          ))}
        </Space>
      )
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button type="link" icon={<EditOutlined />}>
          编辑标签
        </Button>
      )
    }
  ]

  return (
    <div>
      <Card
        title="图片打标"
        extra={
          <Button type="primary" icon={<TagsOutlined />}>
            批量打标
          </Button>
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

export default ImageTagging

