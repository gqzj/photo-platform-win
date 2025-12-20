import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Tag,
  Progress
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, PlayCircleOutlined, SyncOutlined, ReloadOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Option } = Select
const { TextArea } = Input

const TaggingTask = () => {
  const [dataSource, setDataSource] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  })
  const [filters, setFilters] = useState({
    keyword: '',
    status: ''
  })
  const [modalVisible, setModalVisible] = useState(false)
  const [editingRecord, setEditingRecord] = useState(null)
  const [form] = Form.useForm()
  const [selectedRowKeys, setSelectedRowKeys] = useState([])
  const [features, setFeatures] = useState([]) // 特征列表
  const [autoRefresh, setAutoRefresh] = useState(false) // 自动刷新标志

  // 获取特征列表
  const fetchFeatures = async () => {
    try {
      const response = await api.get('/features', { params: { page: 1, page_size: 1000 } })
      if (response.code === 200) {
        setFeatures(response.data.list || [])
      }
    } catch (error) {
      console.error('获取特征列表失败:', error)
    }
  }

  // 获取列表数据
  const fetchData = async (page = 1, pageSize = 20) => {
    setLoading(true)
    try {
      const params = {
        page,
        page_size: pageSize,
        keyword: filters.keyword || undefined,
        status: filters.status || undefined
      }
      
      const response = await api.get('/tagging/tasks', { params })
      if (response.code === 200) {
        setDataSource(response.data.list)
        setPagination({
          current: response.data.page,
          pageSize: response.data.page_size,
          total: response.data.total
        })
      } else {
        message.error(response.message || '获取数据失败')
      }
    } catch (error) {
      message.error('获取数据失败：' + (error.response?.data?.message || error.message))
      console.error('获取数据错误:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData(pagination.current, pagination.pageSize)
    fetchFeatures()
  }, [])

  useEffect(() => {
    fetchData(1, pagination.pageSize)
  }, [filters])

  // 打开新增/编辑弹窗
  const handleOpenModal = (record = null) => {
    setEditingRecord(record)
    if (record) {
      form.setFieldsValue({
        name: record.name,
        description: record.description,
        tagging_features: record.tagging_features || [],
        filter_keywords: record.filter_keywords || [],
        note: record.note
      })
    } else {
      form.resetFields()
      form.setFieldsValue({
        tagging_features: [],
        filter_keywords: []
      })
    }
    setModalVisible(true)
  }

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      
      if (editingRecord) {
        // 更新
        const response = await api.put(`/tagging/tasks/${editingRecord.id}`, values)
        if (response.code === 200) {
          message.success('更新成功')
          setModalVisible(false)
          fetchData(pagination.current, pagination.pageSize)
        } else {
          message.error(response.message || '更新失败')
        }
      } else {
        // 新增
        const response = await api.post('/tagging/tasks', values)
        if (response.code === 200) {
          message.success('创建成功')
          setModalVisible(false)
          fetchData(pagination.current, pagination.pageSize)
        } else {
          message.error(response.message || '创建失败')
        }
      }
    } catch (error) {
      if (error.errorFields) {
        return // 表单验证错误，不显示消息
      }
      message.error('操作失败：' + (error.response?.data?.message || error.message))
      console.error('提交表单错误:', error)
    }
  }

  // 删除
  const handleDelete = async (id) => {
    try {
      const response = await api.delete(`/tagging/tasks/${id}`)
      if (response.code === 200) {
        message.success('删除成功')
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error(response.message || '删除失败')
      }
    } catch (error) {
      message.error('删除失败：' + (error.response?.data?.message || error.message))
      console.error('删除错误:', error)
    }
  }

  // 批量删除
  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要删除的任务')
      return
    }
    
    try {
      const response = await api.delete('/tagging/tasks/batch', {
        data: { ids: selectedRowKeys }
      })
      if (response.code === 200) {
        message.success(response.message || '批量删除成功')
        setSelectedRowKeys([])
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error(response.message || '批量删除失败')
      }
    } catch (error) {
      message.error('批量删除失败：' + (error.response?.data?.message || error.message))
      console.error('批量删除错误:', error)
    }
  }

  // 启动任务
  const handleExecute = async (record) => {
    try {
      const response = await api.post(`/tagging/tasks/${record.id}/execute`)
      if (response.code === 200) {
        message.success('任务已开始执行')
        fetchData(pagination.current, pagination.pageSize)
        // 如果有运行中的任务，开启自动刷新
        setAutoRefresh(true)
      } else {
        message.error(response.message || '启动任务失败')
      }
    } catch (error) {
      message.error('启动任务失败：' + (error.response?.data?.message || error.message))
      console.error('启动任务错误:', error)
    }
  }

  // 重置任务
  const handleReset = async (record) => {
    try {
      const response = await api.post(`/tagging/tasks/${record.id}/reset`)
      if (response.code === 200) {
        message.success('任务重置成功')
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error(response.message || '重置任务失败')
      }
    } catch (error) {
      message.error('重置任务失败：' + (error.response?.data?.message || error.message))
      console.error('重置任务错误:', error)
    }
  }

  // 自动刷新（当有任务在运行时）
  useEffect(() => {
    let interval = null
    if (autoRefresh) {
      // 检查是否有运行中的任务
      const hasRunningTask = dataSource.some(item => item.status === 'running')
      if (hasRunningTask) {
        interval = setInterval(() => {
          fetchData(pagination.current, pagination.pageSize)
        }, 5000) // 每5秒刷新一次
      } else {
        setAutoRefresh(false)
      }
    }
    return () => {
      if (interval) {
        clearInterval(interval)
      }
    }
  }, [autoRefresh, dataSource, pagination])

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80
    },
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      width: 200
    },
    {
      title: '任务说明',
      dataIndex: 'description',
      key: 'description',
      width: 200,
      ellipsis: true,
      render: (text) => text || <span style={{ color: '#999' }}>无</span>
    },
    {
      title: '打标特征',
      dataIndex: 'tagging_features',
      key: 'tagging_features',
      width: 200,
      render: (featureIds) => {
        if (!featureIds || !Array.isArray(featureIds) || featureIds.length === 0) {
          return <span style={{ color: '#999' }}>无</span>
        }
        // 根据特征ID查找特征名称
        const featureMap = {}
        features.forEach(f => {
          featureMap[f.id] = f.name
        })
        return (
          <Space wrap>
            {featureIds.slice(0, 3).map((id, idx) => (
              <Tag key={idx} color="blue">{featureMap[id] || `ID:${id}`}</Tag>
            ))}
            {featureIds.length > 3 && <Tag>+{featureIds.length - 3}</Tag>}
          </Space>
        )
      }
    },
    {
      title: '筛选条件',
      dataIndex: 'filter_keywords',
      key: 'filter_keywords',
      width: 200,
      render: (keywords) => {
        if (!keywords || !Array.isArray(keywords) || keywords.length === 0) {
          return <span style={{ color: '#999' }}>无</span>
        }
        return (
          <Space wrap>
            {keywords.slice(0, 3).map((keyword, idx) => (
              <Tag key={idx} color="green">{keyword}</Tag>
            ))}
            {keywords.length > 3 && <Tag>+{keywords.length - 3}</Tag>}
          </Space>
        )
      }
    },
    {
      title: '打标进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 150,
      render: (progress, record) => {
        const percent = record.progress || 0
        return (
          <Progress
            percent={percent}
            size="small"
            status={record.status === 'running' ? 'active' : 'normal'}
            format={(percent) => `${percent}%`}
          />
        )
      }
    },
    {
      title: '任务状态',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status) => {
        const statusMap = {
          'pending': { color: 'default', text: '待处理' },
          'running': { color: 'processing', text: '运行中' },
          'paused': { color: 'warning', text: '已暂停' },
          'completed': { color: 'success', text: '已完成' },
          'failed': { color: 'error', text: '失败' }
        }
        const statusInfo = statusMap[status] || { color: 'default', text: status }
        return <Tag color={statusInfo.color}>{statusInfo.text}</Tag>
      }
    },
    {
      title: '已处理/总数',
      key: 'count',
      width: 120,
      render: (_, record) => {
        return `${record.processed_count || 0} / ${record.total_count || 0}`
      }
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
      width: 200,
      fixed: 'right',
      render: (_, record) => {
        const canEdit = record.status === 'pending' || record.status === 'failed'
        const canExecute = record.status === 'pending' || record.status === 'failed'
        const canReset = record.status === 'completed' || record.status === 'failed'
        return (
          <Space>
            {canExecute && (
              <Button
                type="link"
                size="small"
                icon={<PlayCircleOutlined />}
                onClick={() => handleExecute(record)}
              >
                启动
              </Button>
            )}
            {canReset && (
              <Popconfirm
                title="确定要重置这个任务吗？重置后将清空所有进度和错误信息。"
                onConfirm={() => handleReset(record)}
                okText="确定"
                cancelText="取消"
              >
                <Button
                  type="link"
                  size="small"
                  icon={<ReloadOutlined />}
                >
                  重置
                </Button>
              </Popconfirm>
            )}
            {canEdit && (
              <Button
                type="link"
                size="small"
                icon={<EditOutlined />}
                onClick={() => handleOpenModal(record)}
              >
                编辑
              </Button>
            )}
            {(record.status === 'pending' || record.status === 'failed' || record.status === 'completed') && (
              <Popconfirm
                title="确定要删除这个任务吗？"
                onConfirm={() => handleDelete(record.id)}
                okText="确定"
                cancelText="取消"
              >
                <Button
                  type="link"
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                >
                  删除
                </Button>
              </Popconfirm>
            )}
          </Space>
        )
      }
    }
  ]

  const rowSelection = {
    selectedRowKeys,
    onChange: setSelectedRowKeys,
    getCheckboxProps: (record) => ({
      disabled: record.status === 'running'
    })
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <Input
              placeholder="搜索任务名称"
              prefix={<SearchOutlined />}
              style={{ width: 200 }}
              value={filters.keyword}
              onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
              allowClear
            />
            <Select
              placeholder="选择状态"
              style={{ width: 150 }}
              value={filters.status}
              onChange={(value) => setFilters({ ...filters, status: value })}
              allowClear
            >
              <Option value="pending">待处理</Option>
              <Option value="running">运行中</Option>
              <Option value="paused">已暂停</Option>
              <Option value="completed">已完成</Option>
              <Option value="failed">失败</Option>
            </Select>
          </Space>
          <Space>
            {selectedRowKeys.length > 0 && (
              <Popconfirm
                title={`确定要删除选中的 ${selectedRowKeys.length} 个任务吗？`}
                onConfirm={handleBatchDelete}
                okText="确定"
                cancelText="取消"
              >
                <Button danger>批量删除</Button>
              </Popconfirm>
            )}
            <Button 
              icon={<SyncOutlined />} 
              onClick={() => fetchData(pagination.current, pagination.pageSize)}
              loading={loading}
            >
              刷新
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
              新建任务
            </Button>
          </Space>
        </div>

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
          rowSelection={rowSelection}
          scroll={{ x: 1500 }}
        />
      </Card>

      <Modal
        title={editingRecord ? '编辑数据打标任务' : '新建数据打标任务'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={800}
        okText="确定"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            tagging_features: [],
            filter_keywords: []
          }}
        >
          <Form.Item
            label="任务名称"
            name="name"
            rules={[{ required: true, message: '请输入任务名称' }]}
          >
            <Input placeholder="请输入任务名称" />
          </Form.Item>

          <Form.Item
            label="任务说明"
            name="description"
          >
            <TextArea
              rows={3}
              placeholder="请输入任务说明（可选）"
            />
          </Form.Item>

          <Form.Item
            label="打标特征"
            name="tagging_features"
            tooltip="选择要打标的特征，可以多选"
          >
            <Select
              mode="multiple"
              placeholder="请选择打标特征"
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
            >
              {features.map(feature => (
                <Option key={feature.id} value={feature.id} label={feature.name}>
                  {feature.name} {feature.category ? `(${feature.category})` : ''}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label="筛选条件（关键字列表）"
            name="filter_keywords"
            tooltip="输入关键字，用于筛选要打标的图片，多个关键字用回车分隔"
          >
            <Select
              mode="tags"
              placeholder="请输入关键字，按回车添加"
              open={false}
              tokenSeparators={[',']}
            />
          </Form.Item>

          <Form.Item
            label="备注"
            name="note"
          >
            <TextArea
              rows={2}
              placeholder="请输入备注（可选）"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default TaggingTask
