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
  Row,
  Col
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, ThunderboltOutlined, EyeOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

const { TextArea } = Input
const { Option } = Select

const FeatureStyleDefinitionManagement = () => {
  const navigate = useNavigate()
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
  const [dimensions, setDimensions] = useState([])
  const [features, setFeatures] = useState([]) // 特征列表（只包含启用的）

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
      
      const response = await api.get('/feature-style-definitions', { params })
      if (response.code === 200) {
        setDataSource(response.data.list)
        setPagination({
          current: response.data.page,
          pageSize: response.data.page_size,
          total: response.data.total
        })
      } else {
        message.error(response.message || '获取列表失败')
      }
    } catch (error) {
      message.error('获取列表失败：' + (error.response?.data?.message || error.message))
    } finally {
      setLoading(false)
    }
  }

  // 获取特征列表（只获取启用的）
  const fetchFeatures = async () => {
    try {
      const response = await api.get('/features', {
        params: {
          page: 1,
          page_size: 1000, // 获取所有特征
          status: 'active' // 只获取启用的特征
        }
      })
      if (response.code === 200) {
        // 过滤掉禁用的特征
        const enabledFeatures = response.data.list.filter(f => f.enabled !== false && f.status !== 'inactive')
        setFeatures(enabledFeatures)
      }
    } catch (error) {
      console.error('获取特征列表失败:', error)
    }
  }

  useEffect(() => {
    fetchData(pagination.current, pagination.pageSize)
  }, [filters])

  useEffect(() => {
    fetchFeatures() // 加载特征列表（只加载一次）
  }, [])

  // 打开新增/编辑模态框
  const handleOpenModal = async (record = null) => {
    setEditingRecord(record)
    if (record) {
      form.setFieldsValue({
        name: record.name,
        description: record.description,
        status: record.status
      })
      // 加载维度数据，需要匹配特征ID
      const dimensionsData = record.dimensions || []
      const dimensionsWithFeatureId = dimensionsData.map(dim => {
        // 根据维度名称查找对应的特征ID
        const feature = features.find(f => f.name === dim.dimension_name)
        return {
          ...dim,
          feature_id: feature ? feature.id : null
        }
      })
      setDimensions(dimensionsWithFeatureId)
    } else {
      form.resetFields()
      setDimensions([])
    }
    setModalVisible(true)
  }

  // 添加维度
  const handleAddDimension = () => {
    setDimensions([...dimensions, { feature_id: null, dimension_name: '', values: [] }])
  }

  // 删除维度
  const handleRemoveDimension = (index) => {
    const newDimensions = dimensions.filter((_, i) => i !== index)
    setDimensions(newDimensions)
  }

  // 更新维度（选择特征）
  const handleDimensionFeatureChange = (index, featureId) => {
    const newDimensions = [...dimensions]
    const feature = features.find(f => f.id === featureId)
    if (feature) {
      newDimensions[index].feature_id = featureId
      newDimensions[index].dimension_name = feature.name
      // 从特征的values_json中获取特征值
      let featureValues = []
      if (feature.values_json) {
        try {
          const valuesData = typeof feature.values_json === 'string' 
            ? JSON.parse(feature.values_json) 
            : feature.values_json
          if (Array.isArray(valuesData)) {
            featureValues = valuesData
          } else if (typeof valuesData === 'object' && valuesData !== null) {
            // 如果是对象，提取值
            featureValues = Object.values(valuesData)
          }
        } catch (e) {
          console.error('解析特征值失败:', e)
        }
      }
      newDimensions[index].values = featureValues
    }
    setDimensions(newDimensions)
  }

  // 更新维度值（多选）
  const handleDimensionValuesChange = (index, selectedValues) => {
    const newDimensions = [...dimensions]
    newDimensions[index].values = selectedValues || []
    setDimensions(newDimensions)
  }

  // 保存
  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      
      // 验证维度
      if (dimensions.length === 0) {
        message.warning('请至少添加一个维度')
        return
      }
      
      for (let i = 0; i < dimensions.length; i++) {
        const dim = dimensions[i]
        if (!dim.dimension_name) {
          message.warning(`第 ${i + 1} 个维度名称不能为空`)
          return
        }
        if (!dim.values || dim.values.length === 0) {
          message.warning(`第 ${i + 1} 个维度至少需要一个值`)
          return
        }
      }
      
      const data = {
        ...values,
        dimensions: dimensions
      }
      
      if (editingRecord) {
        const response = await api.put(`/feature-style-definitions/${editingRecord.id}`, data)
        if (response.code === 200) {
          message.success('更新成功')
          setModalVisible(false)
          fetchData(pagination.current, pagination.pageSize)
        } else {
          message.error(response.message || '更新失败')
        }
      } else {
        const response = await api.post('/feature-style-definitions', data)
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
        return
      }
      message.error('保存失败：' + (error.response?.data?.message || error.message))
    }
  }

  // 删除
  const handleDelete = async (id) => {
    try {
      const response = await api.delete(`/feature-style-definitions/${id}`)
      if (response.code === 200) {
        message.success('删除成功')
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error(response.message || '删除失败')
      }
    } catch (error) {
      message.error('删除失败：' + (error.response?.data?.message || error.message))
    }
  }

  // 生成子风格
  const handleGenerateSubStyles = async (record) => {
    try {
      message.loading({ content: '正在生成子风格...', key: 'generateSubStyles', duration: 0 })
      const response = await api.post(`/feature-style-definitions/${record.id}/generate-sub-styles`)
      if (response.code === 200) {
        message.success({ 
          content: `子风格生成成功！共生成 ${response.data.created_count} 个子风格`, 
          key: 'generateSubStyles',
          duration: 3
        })
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error({ content: response.message || '生成失败', key: 'generateSubStyles', duration: 3 })
      }
    } catch (error) {
      message.error({ 
        content: '生成失败：' + (error.response?.data?.message || error.message), 
        key: 'generateSubStyles',
        duration: 5
      })
    }
  }

  // 查看子风格列表
  const handleViewSubStyles = (record) => {
    navigate(`/style/feature-style-definition/${record.id}/sub-styles`)
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
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: '维度数量',
      dataIndex: 'dimensions',
      key: 'dimensions',
      width: 100,
      render: (dimensions) => dimensions ? dimensions.length : 0
    },
    {
      title: '子风格数量',
      dataIndex: 'sub_style_count',
      key: 'sub_style_count',
      width: 120
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
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
      width: 300,
      fixed: 'right',
      render: (_, record) => (
        <Space wrap size="small">
          <Button
            type="link"
            size="small"
            icon={<ThunderboltOutlined />}
            onClick={() => handleGenerateSubStyles(record)}
            title="生成子风格"
          >
            生成子风格
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewSubStyles(record)}
            disabled={!record.sub_style_count || record.sub_style_count === 0}
            title="查看子风格"
          >
            查看子风格
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
            title="编辑"
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              title="删除"
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
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* 搜索栏 */}
          <Space>
            <Input
              placeholder="搜索名称或描述"
              prefix={<SearchOutlined />}
              value={filters.keyword}
              onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
              style={{ width: 200 }}
              allowClear
            />
            <Select
              placeholder="状态"
              value={filters.status}
              onChange={(value) => setFilters({ ...filters, status: value })}
              style={{ width: 120 }}
              allowClear
            >
              <Option value="active">启用</Option>
              <Option value="inactive">禁用</Option>
            </Select>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
              新增
            </Button>
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

      {/* 新增/编辑模态框 */}
      <Modal
        title={editingRecord ? '编辑特征风格定义' : '新增特征风格定义'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
          setDimensions([])
        }}
        onOk={handleSave}
        width={800}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入名称' }]}
          >
            <Input placeholder="请输入名称" />
          </Form.Item>
          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={3} placeholder="请输入描述" />
          </Form.Item>
          <Form.Item
            name="status"
            label="状态"
            initialValue="active"
          >
            <Select>
              <Option value="active">启用</Option>
              <Option value="inactive">禁用</Option>
            </Select>
          </Form.Item>
          
          {/* 维度配置 */}
          <Form.Item label="维度配置">
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              {dimensions.map((dim, index) => {
                // 获取当前维度对应的特征
                const selectedFeature = features.find(f => f.id === dim.feature_id)
                // 获取特征值列表
                let featureValues = []
                if (selectedFeature && selectedFeature.values_json) {
                  try {
                    const valuesData = typeof selectedFeature.values_json === 'string' 
                      ? JSON.parse(selectedFeature.values_json) 
                      : selectedFeature.values_json
                    if (Array.isArray(valuesData)) {
                      featureValues = valuesData
                    } else if (typeof valuesData === 'object' && valuesData !== null) {
                      featureValues = Object.values(valuesData)
                    }
                  } catch (e) {
                    console.error('解析特征值失败:', e)
                  }
                }
                
                return (
                  <Card key={index} size="small" title={`维度 ${index + 1}`} extra={
                    <Button type="link" danger size="small" onClick={() => handleRemoveDimension(index)}>
                      删除
                    </Button>
                  }>
                    <Row gutter={16}>
                      <Col span={12}>
                        <div style={{ marginBottom: 8 }}>选择特征：</div>
                        <Select
                          placeholder="请选择特征"
                          value={dim.feature_id}
                          onChange={(value) => handleDimensionFeatureChange(index, value)}
                          style={{ width: '100%' }}
                          showSearch
                          filterOption={(input, option) =>
                            (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                          }
                        >
                          {features.map(feature => (
                            <Option key={feature.id} value={feature.id} label={feature.name}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span>{feature.name}</span>
                                {feature.category && (
                                  <Tag color="blue" style={{ marginLeft: 8, fontSize: 12 }}>
                                    {feature.category}
                                  </Tag>
                                )}
                              </div>
                            </Option>
                          ))}
                        </Select>
                      </Col>
                      <Col span={12}>
                        <div style={{ marginBottom: 8 }}>选择特征值：</div>
                        <Select
                          mode="multiple"
                          placeholder={selectedFeature ? "请选择特征值" : "请先选择特征"}
                          value={dim.values || []}
                          onChange={(values) => handleDimensionValuesChange(index, values)}
                          style={{ width: '100%' }}
                          disabled={!selectedFeature || featureValues.length === 0}
                        >
                          {featureValues.map((value, idx) => (
                            <Option key={idx} value={value}>
                              {value}
                            </Option>
                          ))}
                        </Select>
                        {selectedFeature && featureValues.length === 0 && (
                          <div style={{ color: '#999', fontSize: 12, marginTop: 4 }}>
                            该特征没有定义特征值
                          </div>
                        )}
                      </Col>
                    </Row>
                  </Card>
                )
              })}
              <Button type="dashed" onClick={handleAddDimension} block>
                + 添加维度
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default FeatureStyleDefinitionManagement
