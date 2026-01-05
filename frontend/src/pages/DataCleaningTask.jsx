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
  Checkbox,
  Progress
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, PlayCircleOutlined, ReloadOutlined, SyncOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Option } = Select
const { TextArea } = Input

const DataCleaningTask = () => {
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

  // 筛选特征选项
  const filterFeatureOptions = [
    { label: '无人脸', value: 'no_face' },
    { label: '多人脸', value: 'multiple_faces' },
    { label: '无人物', value: 'no_person' },
    { label: '多人物', value: 'multiple_persons' },
    { label: '包含文字', value: 'contains_text' },
    { label: '图片模糊', value: 'blurry' }
  ]

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
      
      const response = await api.get('/data-cleaning/tasks', { params })
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
  }, [])

  useEffect(() => {
    fetchData(1, pagination.pageSize)
  }, [filters])

  // 自动刷新：如果有任务正在运行，每5秒刷新一次
  useEffect(() => {
    const hasRunningTask = dataSource.some(task => task.status === 'running')
    if (hasRunningTask) {
      const interval = setInterval(() => {
        fetchData(pagination.current, pagination.pageSize)
      }, 5000) // 每5秒刷新一次
      
      return () => clearInterval(interval)
    }
  }, [dataSource, pagination.current, pagination.pageSize])

  // 手动刷新
  const handleRefresh = () => {
    fetchData(pagination.current, pagination.pageSize)
    message.success('已刷新')
  }

  // 打开新增/编辑弹窗
  const handleOpenModal = (record = null) => {
    setEditingRecord(record)
    if (record) {
      form.setFieldsValue({
        name: record.name,
        filter_features: record.filter_features || [],
        filter_keywords: record.filter_keywords || [],
        note: record.note
        // status 和 processed_count 不从前端设置，由系统自动管理
      })
    } else {
      form.resetFields()
      form.setFieldsValue({
        filter_features: [],
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
        const response = await api.put(`/data-cleaning/tasks/${editingRecord.id}`, values)
        if (response.code === 200) {
          message.success('更新成功')
          setModalVisible(false)
          fetchData(pagination.current, pagination.pageSize)
        } else {
          message.error(response.message || '更新失败')
        }
      } else {
        // 新增
        const response = await api.post('/data-cleaning/tasks', values)
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

  // 执行任务
  const handleExecute = async (id) => {
    try {
      const response = await api.post(`/data-cleaning/tasks/${id}/execute`)
      if (response.code === 200) {
        message.success('任务已启动，正在后台执行')
        // 刷新列表
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error(response.message || '启动任务失败')
      }
    } catch (error) {
      message.error('启动任务失败：' + (error.response?.data?.message || error.message))
      console.error('启动任务错误:', error)
    }
  }

  // 重置任务
  const handleReset = async (id) => {
    try {
      const response = await api.post(`/data-cleaning/tasks/${id}/reset`)
      if (response.code === 200) {
        message.success('任务重置成功')
        // 刷新列表
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error(response.message || '重置任务失败')
      }
    } catch (error) {
      message.error('重置任务失败：' + (error.response?.data?.message || error.message))
      console.error('重置任务错误:', error)
    }
  }

  // 删除
  const handleDelete = async (id) => {
    try {
      const response = await api.delete(`/data-cleaning/tasks/${id}`)
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
      const response = await api.delete('/data-cleaning/tasks/batch', {
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
      title: '筛选特征',
      dataIndex: 'filter_features',
      key: 'filter_features',
      width: 200,
      render: (features) => {
        if (!features || !Array.isArray(features) || features.length === 0) {
          return <span style={{ color: '#999' }}>无</span>
        }
        // 将英文值映射为中文标签
        const featureMap = {
          'no_face': '无人脸',
          'multiple_faces': '多人脸',
          'no_person': '无人物',
          'multiple_persons': '多人物',
          'contains_text': '包含文字',
          'blurry': '图片模糊'
        }
        return (
          <Space wrap>
            {features.map((feature, idx) => (
              <Tag key={idx} color="blue">{featureMap[feature] || feature}</Tag>
            ))}
          </Space>
        )
      }
    },
    {
      title: '筛选范围',
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
      title: '进度',
      key: 'progress',
      width: 200,
      render: (_, record) => {
        const { processed_count = 0, total_count = 0 } = record
        const percentage = total_count > 0 ? Math.round((processed_count / total_count) * 100) : 0
        return (
          <div>
            <div style={{ marginBottom: 4 }}>
              {processed_count} / {total_count}
            </div>
            <Progress 
              percent={percentage} 
              size="small"
              status={record.status === 'running' ? 'active' : record.status === 'completed' ? 'success' : 'normal'}
            />
          </div>
        )
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
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          {(record.status === 'pending' || record.status === 'failed') && (
            <Button
              type="link"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => handleExecute(record.id)}
            >
              执行
            </Button>
          )}
          {(record.status === 'completed' || record.status === 'failed' || record.status === 'running') && (
            <Popconfirm
              title={record.status === 'running' ? "确定要重置这个运行中的任务吗？重置后任务将停止执行，可以重新执行。" : "确定要重置这个任务吗？重置后可以重新执行。"}
              onConfirm={() => handleReset(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="link"
                size="small"
                icon={<ReloadOutlined />}
                danger={record.status === 'running'}
              >
                重置
              </Button>
            </Popconfirm>
          )}
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
            disabled={record.status === 'running'}
          >
            编辑
          </Button>
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
        </Space>
      )
    }
  ]

  return (
    <div>
      <Card
        title="数据清洗任务管理"
        extra={
          <Space>
            <Button 
              icon={<SyncOutlined />} 
              onClick={handleRefresh}
              loading={loading}
            >
              刷新
            </Button>
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
            <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
              新增任务
            </Button>
          </Space>
        }
      >
        {/* 搜索栏 */}
        <Space style={{ marginBottom: 16 }} wrap>
          <Input
            placeholder="搜索任务名称"
            prefix={<SearchOutlined />}
            style={{ width: 250 }}
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
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, pageSize) => {
              fetchData(page, pageSize)
            },
            onShowSizeChange: (current, size) => {
              fetchData(1, size)
            }
          }}
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys
          }}
          scroll={{ x: 1400 }}
        />
      </Card>

      {/* 新增/编辑弹窗 */}
      <Modal
        title={editingRecord ? '编辑数据清洗任务' : '新增数据清洗任务'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
        }}
        width={700}
        okText="确定"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            filter_features: [],
            filter_keywords: []
          }}
        >
          <Form.Item
            name="name"
            label="任务名称"
            rules={[{ required: true, message: '请输入任务名称' }]}
          >
            <Input placeholder="请输入任务名称" />
          </Form.Item>

          <Form.Item
            name="filter_features"
            label="筛选特征"
            tooltip="选择需要筛选的特征条件"
          >
            <Checkbox.Group options={filterFeatureOptions} />
          </Form.Item>

          <Form.Item
            name="filter_keywords"
            label="筛选范围（关键字列表）"
            tooltip="输入关键字，按回车或逗号分隔添加多个关键字"
          >
            <Select
              mode="tags"
              placeholder="请输入关键字，按回车添加"
              style={{ width: '100%' }}
              tokenSeparators={[',']}
              open={false}
            />
          </Form.Item>

          <Form.Item
            name="note"
            label="备注"
          >
            <TextArea
              placeholder="请输入备注信息"
              rows={3}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default DataCleaningTask