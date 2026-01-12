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
  Switch
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Option } = Select
const { TextArea } = Input

const FeatureManagement = () => {
  const [dataSource, setDataSource] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  })
  const [filters, setFilters] = useState({
    keyword: '',
    category: '',
    status: ''
  })
  const [modalVisible, setModalVisible] = useState(false)
  const [editingRecord, setEditingRecord] = useState(null)
  const [form] = Form.useForm()
  const [categories, setCategories] = useState([])
  const [selectedRowKeys, setSelectedRowKeys] = useState([])

  // 获取分类列表
  const fetchCategories = async () => {
    try {
      const response = await api.get('/features/categories')
      if (response.code === 200) {
        setCategories(response.data || [])
      }
    } catch (error) {
      console.error('获取分类列表失败:', error)
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
        category: filters.category || undefined,
        status: filters.status || undefined
      }
      
      const response = await api.get('/features', { params })
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
    fetchCategories()
  }, [])

  useEffect(() => {
    fetchData(1, pagination.pageSize)
  }, [filters])

  // 打开新增/编辑弹窗
  const handleOpenModal = (record = null) => {
    setEditingRecord(record)
    if (record) {
      // 解析values_json为数组
      let values = []
      if (record.values_json) {
        try {
          values = JSON.parse(record.values_json)
          if (!Array.isArray(values)) {
            values = []
          }
        } catch (e) {
          values = []
        }
      }
      form.setFieldsValue({
        ...record,
        values: values
      })
    } else {
      form.resetFields()
      form.setFieldsValue({
        status: 'active',
        enabled: true,
        auto_tagging: false,
        values: []
      })
    }
    setModalVisible(true)
  }

  // 提交表单
  const handleSubmit = async () => {
    try {
      const formValues = await form.validateFields()
      
      // 将values数组转换为JSON字符串
      const submitData = { ...formValues }
      if (formValues.values && Array.isArray(formValues.values)) {
        submitData.values_json = JSON.stringify(formValues.values.filter(v => v && v.trim()))
      } else {
        submitData.values_json = null
      }
      delete submitData.values
      
      if (editingRecord) {
        // 更新
        const response = await api.put(`/features/${editingRecord.id}`, submitData)
        if (response.code === 200) {
          message.success('更新成功')
          setModalVisible(false)
          fetchData(pagination.current, pagination.pageSize)
        } else {
          message.error(response.message || '更新失败')
        }
      } else {
        // 新增
        const response = await api.post('/features', submitData)
        if (response.code === 200) {
          message.success('创建成功')
          setModalVisible(false)
          fetchData(pagination.current, pagination.pageSize)
          fetchCategories() // 刷新分类列表
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
      const response = await api.delete(`/features/${id}`)
      if (response.code === 200) {
        message.success('删除成功')
        fetchData(pagination.current, pagination.pageSize)
        fetchCategories() // 刷新分类列表
      } else {
        message.error(response.message || '删除失败')
      }
    } catch (error) {
      message.error('删除失败：' + (error.response?.data?.message || error.message))
      console.error('删除错误:', error)
    }
  }

  // 启用/禁用特征
  const handleToggleStatus = async (record) => {
    try {
      const newStatus = record.status === 'active' ? 'inactive' : 'active'
      const response = await api.put(`/features/${record.id}`, {
        status: newStatus
      })
      if (response.code === 200) {
        message.success(newStatus === 'active' ? '启用成功' : '禁用成功')
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error(response.message || '操作失败')
      }
    } catch (error) {
      message.error('操作失败：' + (error.response?.data?.message || error.message))
      console.error('启用/禁用特征错误:', error)
    }
  }

  // 批量删除
  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要删除的特征')
      return
    }
    
    try {
      const response = await api.delete('/features/batch', {
        data: { ids: selectedRowKeys }
      })
      if (response.code === 200) {
        message.success(response.message || '批量删除成功')
        setSelectedRowKeys([])
        fetchData(pagination.current, pagination.pageSize)
        fetchCategories() // 刷新分类列表
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
      title: '特征名称',
      dataIndex: 'name',
      key: 'name',
      width: 200
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 150,
      render: (text) => text || '-'
    },
    {
      title: '特征值',
      dataIndex: 'values_json',
      key: 'values_json',
      width: 300,
      render: (values_json) => {
        if (!values_json) {
          return <span style={{ color: '#999' }}>无</span>
        }
        let values = []
        try {
          const parsed = typeof values_json === 'string' ? JSON.parse(values_json) : values_json
          values = Array.isArray(parsed) ? parsed : []
        } catch (e) {
          // 如果不是JSON格式，尝试作为字符串处理
          values = []
        }
        
        if (values.length === 0) {
          return <span style={{ color: '#999' }}>无</span>
        }
        
        return (
          <Space wrap>
            {values.map((value, index) => (
              <Tag key={index} color="blue">{value}</Tag>
            ))}
          </Space>
        )
      }
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: '颜色',
      dataIndex: 'color',
      key: 'color',
      width: 100,
      render: (color) => <Tag color={color}>{color}</Tag>
    },
    {
      title: '自动标注',
      dataIndex: 'auto_tagging',
      key: 'auto_tagging',
      width: 100,
      render: (auto_tagging) => (
        <Tag color={auto_tagging ? 'green' : 'default'}>
          {auto_tagging ? '是' : '否'}
        </Tag>
      )
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
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            onClick={() => handleToggleStatus(record)}
          >
            {record.status === 'active' ? '禁用' : '启用'}
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个特征吗？"
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

  // 颜色选项
  const colorOptions = [
    'blue', 'green', 'red', 'orange', 'purple', 'cyan', 'magenta', 'gold', 'lime', 'geekblue', 'volcano'
  ]

  return (
    <div>
      <Card
        title="特征管理"
        extra={
          <Space>
            {selectedRowKeys.length > 0 && (
              <Popconfirm
                title={`确定要删除选中的 ${selectedRowKeys.length} 个特征吗？`}
                onConfirm={handleBatchDelete}
                okText="确定"
                cancelText="取消"
              >
                <Button danger>批量删除</Button>
              </Popconfirm>
            )}
            <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
              新增特征
            </Button>
          </Space>
        }
      >
        {/* 搜索栏 */}
        <Space style={{ marginBottom: 16 }} wrap>
          <Input
            placeholder="搜索特征名称或描述"
            prefix={<SearchOutlined />}
            style={{ width: 250 }}
            value={filters.keyword}
            onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
            allowClear
          />
          <Select
            placeholder="选择分类"
            style={{ width: 150 }}
            value={filters.category}
            onChange={(value) => setFilters({ ...filters, category: value })}
            allowClear
          >
            {categories.map(cat => (
              <Option key={cat} value={cat}>{cat}</Option>
            ))}
          </Select>
          <Select
            placeholder="选择状态"
            style={{ width: 120 }}
            value={filters.status}
            onChange={(value) => setFilters({ ...filters, status: value })}
            allowClear
          >
            <Option value="active">启用</Option>
            <Option value="inactive">禁用</Option>
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
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 新增/编辑弹窗 */}
      <Modal
        title={editingRecord ? '编辑特征' : '新增特征'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
        }}
        width={600}
        okText="确定"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            status: 'active',
            enabled: true,
            auto_tagging: false,
            values: []
          }}
        >
          <Form.Item
            name="name"
            label="特征名称"
            rules={[{ required: true, message: '请输入特征名称' }]}
          >
            <Input placeholder="请输入特征名称" />
          </Form.Item>

          <Form.Item
            name="category"
            label="分类"
          >
            <Select
              placeholder="请选择或输入分类"
              mode="tags"
              style={{ width: '100%' }}
              tokenSeparators={[',']}
            >
              {categories.map(cat => (
                <Option key={cat} value={cat}>{cat}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea
              placeholder="请输入特征描述"
              rows={4}
            />
          </Form.Item>

          <Form.Item
            name="color"
            label="显示颜色"
          >
            <Select placeholder="请选择颜色">
              {colorOptions.map(color => (
                <Option key={color} value={color}>
                  <Tag color={color}>{color}</Tag>
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="auto_tagging"
            label="自动标注"
            valuePropName="checked"
          >
            <Switch checkedChildren="是" unCheckedChildren="否" />
          </Form.Item>

          <Form.Item
            name="values"
            label="特征值"
            tooltip="输入特征值，按回车或逗号分隔添加多个值"
          >
            <Select
              mode="tags"
              placeholder="请输入特征值，按回车添加"
              style={{ width: '100%' }}
              tokenSeparators={[',']}
              open={false}
            />
          </Form.Item>

          <Form.Item
            name="status"
            label="状态"
          >
            <Select>
              <Option value="active">启用</Option>
              <Option value="inactive">禁用</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default FeatureManagement

