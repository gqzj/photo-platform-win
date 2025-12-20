import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  message,
  Popconfirm,
  Tag,
  Select,
  Checkbox
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Option } = Select
const { TextArea } = Input

const RequirementManagement = () => {
  const [dataSource, setDataSource] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  })
  const [filters, setFilters] = useState({
    keyword: '',
    status: '',
    requester: ''
  })
  const [modalVisible, setModalVisible] = useState(false)
  const [editingRecord, setEditingRecord] = useState(null)
  const [form] = Form.useForm()
  const [features, setFeatures] = useState([]) // 特征列表

  // 筛选特征选项（与数据清洗任务保持一致）
  const filterFeatureOptions = [
    { label: '无人脸', value: 'no_face' },
    { label: '多人脸', value: 'multiple_faces' },
    { label: '无人物', value: 'no_person' },
    { label: '多人物', value: 'multiple_persons' },
    { label: '包含文字', value: 'contains_text' },
    { label: '图片模糊', value: 'blurry' }
  ]

  // 获取特征列表
  const fetchFeatures = async () => {
    try {
      const response = await api.get('/features', { params: { page: 1, page_size: 1000, status: 'active' } })
      if (response.code === 200) {
        setFeatures(response.data.list || [])
      }
    } catch (error) {
      console.error('获取特征列表失败:', error)
    }
  }

  useEffect(() => {
    fetchFeatures()
  }, [])

  // 获取数据
  const fetchData = async (page = 1, pageSize = 10) => {
    setLoading(true)
    try {
      const params = {
        page,
        page_size: pageSize,
        ...filters
      }
      const response = await api.get('/requirements', { params })
      if (response.code === 200) {
        setDataSource(response.data.list || [])
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
  }, [filters])

  // 打开模态框
  const handleOpenModal = (record = null) => {
    setEditingRecord(record)
    if (record) {
      form.resetFields()
      form.setFieldsValue({
        name: record.name,
        requester: record.requester,
        keywords: record.keywords || [],
        cleaning_features: record.cleaning_features || [],
        tagging_features: record.tagging_features || [],
        sample_set_features: record.sample_set_features || [],
        status: record.status,
        note: record.note
      })
    } else {
      form.resetFields()
      form.setFieldsValue({
        status: 'pending',
        keywords: [],
        cleaning_features: [],
        tagging_features: [],
        sample_set_features: []
      })
    }
    setModalVisible(true)
  }

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const submitData = {
        name: values.name,
        requester: values.requester || '',
        keywords: values.keywords || [],
        cleaning_features: values.cleaning_features || [],
        tagging_features: values.tagging_features || [],
        sample_set_features: values.sample_set_features || [],
        status: values.status,
        note: values.note || ''
      }

      if (editingRecord) {
        // 更新
        const response = await api.put(`/requirements/${editingRecord.id}`, submitData)
        if (response.code === 200) {
          message.success('更新成功')
          setModalVisible(false)
          fetchData(pagination.current, pagination.pageSize)
        } else {
          message.error(response.message || '更新失败')
        }
      } else {
        // 新增
        const response = await api.post('/requirements', submitData)
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
        return // 表单验证错误
      }
      message.error('操作失败：' + (error.message || '未知错误'))
    }
  }

  // 删除
  const handleDelete = async (id) => {
    try {
      const response = await api.delete(`/requirements/${id}`)
      if (response.code === 200) {
        message.success('删除成功')
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error(response.message || '删除失败')
      }
    } catch (error) {
      message.error('删除失败：' + (error.message || '未知错误'))
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
      title: '需求名称',
      dataIndex: 'name',
      key: 'name',
      width: 200
    },
    {
      title: '需求发起人',
      dataIndex: 'requester',
      key: 'requester',
      width: 120
    },
    {
      title: '关键字',
      dataIndex: 'keywords',
      key: 'keywords',
      width: 200,
      render: (keywords) => {
        if (!keywords || keywords.length === 0) {
          return <span style={{ color: '#999' }}>无</span>
        }
        return (
          <Space wrap>
            {keywords.slice(0, 3).map((keyword, idx) => (
              <Tag key={idx} color="blue">{keyword}</Tag>
            ))}
            {keywords.length > 3 && <Tag>+{keywords.length - 3}</Tag>}
          </Space>
        )
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const colorMap = {
          'pending': 'default',
          'active': 'processing',
          'completed': 'success',
          'cancelled': 'error'
        }
        const textMap = {
          'pending': '待处理',
          'active': '进行中',
          'completed': '已完成',
          'cancelled': '已取消'
        }
        return <Tag color={colorMap[status] || 'default'}>{textMap[status] || status}</Tag>
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
            title="确定要删除这条记录吗？"
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

  // 渲染特征选择组件（用于清洗和样本集）
  const renderFeatureSelector = (fieldName, label) => {
    return (
      <Form.Item
        name={fieldName}
        label={label}
      >
        <Form.List name={fieldName}>
          {(fields, { add, remove }) => (
            <>
              {fields.map((field, index) => (
                <div key={field.key} style={{ marginBottom: 16, padding: 16, border: '1px solid #d9d9d9', borderRadius: 4 }}>
                  <Space style={{ width: '100%', marginBottom: 8 }} align="baseline">
                    <Form.Item
                      {...field}
                      name={[field.name, 'feature_id']}
                      label="特征"
                      rules={[{ required: true, message: '请选择特征' }]}
                    >
                      <Select
                        placeholder="请选择特征"
                        style={{ width: 200 }}
                        onChange={(value) => {
                          const selectedFeature = features.find(f => f.id === value)
                          if (selectedFeature && selectedFeature.values_json) {
                            try {
                              const values = typeof selectedFeature.values_json === 'string'
                                ? JSON.parse(selectedFeature.values_json)
                                : selectedFeature.values_json
                              if (Array.isArray(values) && values.length > 0) {
                                // 如果有预定义值，清空当前值范围，让用户重新选择
                                form.setFieldsValue({
                                  [fieldName]: form.getFieldValue(fieldName).map((item, idx) =>
                                    idx === field.name ? { ...item, value_range: [] } : item
                                  )
                                })
                              }
                            } catch (e) {
                              console.error('解析特征值失败:', e)
                            }
                          }
                        }}
                      >
                        {features.map(feature => (
                          <Option key={feature.id} value={feature.id}>
                            {feature.name}
                          </Option>
                        ))}
                      </Select>
                    </Form.Item>
                    <Form.Item
                      {...field}
                      name={[field.name, 'value_range']}
                      label="特征值范围"
                    >
                      {(() => {
                        const featureId = form.getFieldValue([fieldName, field.name, 'feature_id'])
                        const selectedFeature = features.find(f => f.id === featureId)
                        let featureValues = []
                        if (selectedFeature && selectedFeature.values_json) {
                          try {
                            const values = typeof selectedFeature.values_json === 'string'
                              ? JSON.parse(selectedFeature.values_json)
                              : selectedFeature.values_json
                            if (Array.isArray(values)) {
                              featureValues = values
                            }
                          } catch (e) {
                            console.error('解析特征值失败:', e)
                          }
                        }
                        
                        if (featureValues.length > 0) {
                          return (
                            <Checkbox.Group style={{ width: 400 }}>
                              {featureValues.map(value => (
                                <Checkbox key={value} value={value}>{value}</Checkbox>
                              ))}
                            </Checkbox.Group>
                          )
                        }
                        return <Input placeholder="请输入特征值范围（多个用逗号分隔）" style={{ width: 400 }} />
                      })()}
                    </Form.Item>
                    <Button type="link" danger onClick={() => remove(field.name)}>删除</Button>
                  </Space>
                </div>
              ))}
              <Button type="dashed" onClick={() => add()} block>
                添加特征
              </Button>
            </>
          )}
        </Form.List>
      </Form.Item>
    )
  }

  return (
    <div>
      <Card
        title="需求管理"
        extra={
          <Space>
            <Input
              placeholder="搜索需求名称"
              prefix={<SearchOutlined />}
              style={{ width: 200 }}
              value={filters.keyword}
              onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
              onPressEnter={() => fetchData(1, pagination.pageSize)}
            />
            <Select
              placeholder="状态筛选"
              allowClear
              style={{ width: 120 }}
              value={filters.status}
              onChange={(value) => setFilters({ ...filters, status: value })}
            >
              <Option value="pending">待处理</Option>
              <Option value="active">进行中</Option>
              <Option value="completed">已完成</Option>
              <Option value="cancelled">已取消</Option>
            </Select>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => handleOpenModal()}
            >
              新增需求
            </Button>
          </Space>
        }
      >
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
              fetchData(page, pageSize)
            },
            onShowSizeChange: (current, size) => {
              fetchData(current, size)
            }
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      <Modal
        title={editingRecord ? '编辑需求' : '新增需求'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
        }}
        width={900}
        okText="确定"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            status: 'pending',
            keywords: [],
            cleaning_features: [],
            tagging_features: [],
            sample_set_features: []
          }}
        >
          <Form.Item
            name="name"
            label="需求名称"
            rules={[{ required: true, message: '请输入需求名称' }]}
          >
            <Input placeholder="请输入需求名称" />
          </Form.Item>

          <Form.Item
            name="requester"
            label="需求发起人"
          >
            <Input placeholder="请输入需求发起人" />
          </Form.Item>

          <Form.Item
            name="keywords"
            label="抓取的关键字范围"
            rules={[{ required: true, message: '请至少输入一个关键字' }]}
          >
            <Select
              mode="tags"
              placeholder="请输入关键字，按回车或逗号添加多个"
              tokenSeparators={[',', '，']}
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Form.Item
            name="cleaning_features"
            label="清洗任务的筛选特征"
            tooltip="选择需要筛选的特征条件"
          >
            <Checkbox.Group options={filterFeatureOptions} />
          </Form.Item>

          <Form.Item
            name="tagging_features"
            label="需要打标的特征"
          >
            <Select
              mode="multiple"
              placeholder="请选择需要打标的特征"
              style={{ width: '100%' }}
              onChange={(selectedFeatureIds) => {
                // 当选择打标特征后，自动添加到样本集的特征范围
                if (selectedFeatureIds && selectedFeatureIds.length > 0) {
                  const currentSampleSetFeatures = form.getFieldValue('sample_set_features') || []
                  
                  // 获取新选择的特征
                  const newFeatures = selectedFeatureIds.filter(id => 
                    !currentSampleSetFeatures.some(item => item.feature_id === id)
                  )
                  
                  // 为每个新特征创建配置，默认勾选所有特征值
                  const newSampleSetFeatures = newFeatures.map(featureId => {
                    const feature = features.find(f => f.id === featureId)
                    let valueRange = []
                    
                    // 如果特征有预定义值，默认全部勾选
                    if (feature && feature.values_json) {
                      try {
                        const values = typeof feature.values_json === 'string'
                          ? JSON.parse(feature.values_json)
                          : feature.values_json
                        if (Array.isArray(values) && values.length > 0) {
                          valueRange = values // 默认勾选所有特征值
                        }
                      } catch (e) {
                        console.error('解析特征值失败:', e)
                      }
                    }
                    
                    return {
                      feature_id: featureId,
                      value_range: valueRange
                    }
                  })
                  
                  // 合并到现有的样本集特征中
                  form.setFieldsValue({
                    sample_set_features: [...currentSampleSetFeatures, ...newSampleSetFeatures]
                  })
                }
              }}
            >
              {features.map(feature => (
                <Option key={feature.id} value={feature.id}>
                  {feature.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          {renderFeatureSelector('sample_set_features', '样本集的特征范围')}

          <Form.Item
            name="status"
            label="状态"
            rules={[{ required: true, message: '请选择状态' }]}
          >
            <Select placeholder="请选择状态">
              <Option value="pending">待处理</Option>
              <Option value="active">进行中</Option>
              <Option value="completed">已完成</Option>
              <Option value="cancelled">已取消</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="note"
            label="备注"
          >
            <TextArea
              rows={3}
              placeholder="请输入备注（可选）"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default RequirementManagement

