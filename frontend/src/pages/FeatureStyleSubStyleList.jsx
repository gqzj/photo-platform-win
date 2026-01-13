import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Input,
  message,
  Tag,
  Popconfirm
} from 'antd'
import { SearchOutlined, EyeOutlined, DeleteOutlined, ArrowLeftOutlined } from '@ant-design/icons'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../services/api'

const FeatureStyleSubStyleList = () => {
  const { definitionId } = useParams()
  const navigate = useNavigate()
  const [dataSource, setDataSource] = useState([])
  const [loading, setLoading] = useState(false)
  const [definition, setDefinition] = useState(null)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  })
  const [keyword, setKeyword] = useState('')

  // 获取定义信息
  const fetchDefinition = async () => {
    try {
      const response = await api.get(`/feature-style-definitions/${definitionId}`)
      if (response.code === 200) {
        setDefinition(response.data)
      }
    } catch (error) {
      message.error('获取定义信息失败：' + (error.response?.data?.message || error.message))
    }
  }

  // 获取子风格列表
  const fetchData = async (page = 1, pageSize = 20) => {
    setLoading(true)
    try {
      const params = {
        page,
        page_size: pageSize,
        keyword: keyword || undefined
      }
      
      const response = await api.get(`/feature-style-definitions/${definitionId}/sub-styles`, { params })
      if (response.code === 200) {
        setDataSource(response.data.list)
        setPagination({
          current: response.data.page,
          pageSize: response.data.page_size,
          total: response.data.total
        })
        if (response.data.definition_name) {
          setDefinition({ name: response.data.definition_name })
        }
      } else {
        message.error(response.message || '获取列表失败')
      }
    } catch (error) {
      message.error('获取列表失败：' + (error.response?.data?.message || error.message))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDefinition()
    fetchData(pagination.current, pagination.pageSize)
  }, [definitionId, keyword])

  // 查看子风格图片
  const handleViewImages = (record) => {
    navigate(`/style/feature-style-definition/${definitionId}/sub-styles/${record.id}/images`)
  }

  // 删除子风格
  const handleDelete = async (id) => {
    try {
      // 注意：这里需要添加删除子风格的API，目前先提示
      message.warning('删除子风格功能待实现')
    } catch (error) {
      message.error('删除失败：' + (error.response?.data?.message || error.message))
    }
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 200
    },
    {
      title: '维度值组合',
      dataIndex: 'dimension_values',
      key: 'dimension_values',
      render: (values) => {
        if (!values || typeof values !== 'object') return '-'
        return Object.entries(values).map(([key, value]) => (
          <Tag key={key} style={{ marginBottom: 4 }}>
            {key}: {value}
          </Tag>
        ))
      }
    },
    {
      title: '图片数量',
      dataIndex: 'image_count',
      key: 'image_count',
      width: 100
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space wrap size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewImages(record)}
            title="查看图片"
          >
            查看图片
          </Button>
        </Space>
      )
    }
  ]

  return (
    <div>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 标题和返回 */}
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/style/feature-style-definition')}>
              返回
            </Button>
            <h2 style={{ margin: 0 }}>
              {definition?.name || '特征风格定义'} - 子风格列表
            </h2>
          </Space>

          {/* 搜索栏 */}
          <Space>
            <Input
              placeholder="搜索子风格名称"
              prefix={<SearchOutlined />}
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              style={{ width: 200 }}
              allowClear
            />
          </Space>

          {/* 表格 */}
          <Table
            columns={columns}
            dataSource={dataSource}
            rowKey="id"
            loading={loading}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: pagination.total,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 条`,
              onChange: (page, pageSize) => {
                setPagination({ ...pagination, current: page, pageSize })
                fetchData(page, pageSize)
              }
            }}
            scroll={{ x: 'max-content' }}
          />
        </Space>
      </Card>
    </div>
  )
}

export default FeatureStyleSubStyleList
