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
  Switch,
  Checkbox
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Option } = Select
const { TextArea } = Input

const FeatureGroupManagement = () => {
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
  const [allFeatures, setAllFeatures] = useState([])
  const [selectedRowKeys, setSelectedRowKeys] = useState([])

  // 获取所有特征列表
  const fetchAllFeatures = async () => {
    try {
      const response = await api.get('/features', { params: { page: 1, page_size: 1000 } })
      if (response.code === 200) {
        setAllFeatures(response.data.list || [])
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
      
      const response = await api.get('/feature-groups', { params })
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
    fetchAllFeatures()
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
        status: record.status || 'active',
        enabled: record.enabled !== undefined ? record.enabled : true,
        feature_ids: record.features ? record.features.map(f => f.id) : []
      })
    } else {
      form.resetFields()
      form.setFieldsValue({
        status: 'active',
        enabled: true,
        feature_ids: []
      })
    }
    setModalVisible(true)
  }

  // 提交表单
  const handleSubmit = async () => {
    try {
      const formValues = await form.validateFields()
      
      const submitData = {
        name: formValues.name,
        description: formValues.description,
        enabled: formValues.enabled !== undefined ? formValues.enabled : (formValues.status === 'active'),
        feature_ids: formValues.feature_ids || []
      }
      
      if (editingRecord) {
        // 更新
        const response = await api.put(`/feature-groups/${editingRecord.id}`, submitData)
        if (response.code === 200) {
          message.success('更新成功')
          setModalVisible(false)
          fetchData(pagination.current, pagination.pageSize)
        } else {
          message.error(response.message || '更新失败')
        }
      } else {
        // 新增
        const response = await api.post('/feature-groups', submitData)
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
      const response = await api.delete(`/feature-groups/${id}`)
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
      message.warning('请选择要删除的特征组')
      return
    }
    
    try {
      const response = await api.delete('/feature-groups/batch', {
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
      title: '特征组名称',
      dataIndex: 'name',
      key: 'name',
      width: 200
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: '特征数量',
      dataIndex: 'feature_count',
      key: 'feature_count',
      width: 100,
      render: (count) => count || 0
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => (
        <Tag color={status === 'active' ? 'green' : 'default'}>
          {status === 'active' ? '启用' : '禁用'}
        </Tag>
      )
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
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个特征组吗？"
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
    <Card>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Input
            placeholder="搜索特征组名称或描述"
            prefix={<SearchOutlined />}
            style={{ width: 250 }}
            value={filters.keyword}
            onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
            onPressEnter={() => fetchData(1, pagination.pageSize)}
            allowClear
          />
          <Select
            placeholder="状态筛选"
            style={{ width: 120 }}
            value={filters.status || undefined}
            onChange={(value) => setFilters({ ...filters, status: value })}
            allowClear
          >
            <Option value="active">启用</Option>
            <Option value="inactive">禁用</Option>
          </Select>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleOpenModal()}
          >
            新增特征组
          </Button>
          {selectedRowKeys.length > 0 && (
            <Popconfirm
              title={`确定要删除选中的 ${selectedRowKeys.length} 个特征组吗？`}
              onConfirm={handleBatchDelete}
              okText="确定"
              cancelText="取消"
            >
              <Button danger>
                批量删除 ({selectedRowKeys.length})
              </Button>
            </Popconfirm>
          )}
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={dataSource}
        loading={loading}
        rowKey="id"
        rowSelection={{
          selectedRowKeys,
          onChange: setSelectedRowKeys
        }}
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
        scroll={{ x: 1200 }}
      />

      <Modal
        title={editingRecord ? '编辑特征组' : '新增特征组'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            status: 'active',
            enabled: true,
            feature_ids: []
          }}
        >
          <Form.Item
            label="特征组名称"
            name="name"
            rules={[{ required: true, message: '请输入特征组名称' }]}
          >
            <Input placeholder="请输入特征组名称" />
          </Form.Item>

          <Form.Item
            label="描述"
            name="description"
          >
            <TextArea
              rows={3}
              placeholder="请输入特征组描述"
            />
          </Form.Item>

          <Form.Item
            label="状态"
            name="status"
            rules={[{ required: true, message: '请选择状态' }]}
          >
            <Select placeholder="请选择状态">
              <Option value="active">启用</Option>
              <Option value="inactive">禁用</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="包含的特征"
            name="feature_ids"
            rules={[{ required: true, message: '请至少选择一个特征' }]}
          >
            <Checkbox.Group style={{ width: '100%' }}>
              <div style={{ maxHeight: '300px', overflowY: 'auto', border: '1px solid #d9d9d9', padding: '8px', borderRadius: '4px' }}>
                {allFeatures.map(feature => (
                  <div key={feature.id} style={{ marginBottom: '8px' }}>
                    <Checkbox value={feature.id}>
                      <span style={{ marginLeft: '8px' }}>
                        {feature.name}
                        {feature.description && (
                          <span style={{ color: '#999', fontSize: '12px', marginLeft: '8px' }}>
                            ({feature.description})
                          </span>
                        )}
                      </span>
                    </Checkbox>
                  </div>
                ))}
              </div>
            </Checkbox.Group>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

export default FeatureGroupManagement

