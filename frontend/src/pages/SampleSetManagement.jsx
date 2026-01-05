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
  Switch,
  InputNumber,
  Checkbox
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, CalculatorOutlined, InboxOutlined, DownloadOutlined, ReloadOutlined, EyeOutlined, CopyOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

const { Option } = Select
const { TextArea } = Input

const SampleSetManagement = () => {
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
  const [selectedRowKeys, setSelectedRowKeys] = useState([])
  const [features, setFeatures] = useState([]) // 特征列表
  const [keywords, setKeywords] = useState([]) // 关键字列表

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

  // 获取关键字列表
  const fetchKeywords = async () => {
    try {
      const response = await api.get('/keyword-statistics', { params: { page: 1, page_size: 1000 } })
      if (response.code === 200) {
        const keywordList = (response.data.list || []).map(item => item.keyword).filter(k => k)
        setKeywords(keywordList)
      }
    } catch (error) {
      console.error('获取关键字列表失败:', error)
    }
  }

  useEffect(() => {
    fetchFeatures()
    fetchKeywords()
  }, [])

  // 获取数据
  const fetchData = async (page = 1, pageSize = 20) => {
    setLoading(true)
    try {
      const params = {
        page,
        page_size: pageSize,
        ...filters
      }
      const response = await api.get('/sample-sets', { params })
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
      // 处理特征数据，确保格式正确
      const featuresData = (record.features || []).map(f => {
        let valueRange = f.value_range
        
        // 如果 value_range 是字符串，尝试解析为 JSON
        if (typeof valueRange === 'string') {
          try {
            valueRange = JSON.parse(valueRange)
          } catch (e) {
            // 解析失败，保持原值
            console.error('解析 value_range 失败:', e)
          }
        }
        
        // 如果是数组，保持数组格式（用于多选框）
        if (Array.isArray(valueRange)) {
          valueRange = valueRange
        }
        
        return {
          feature_id: f.feature_id,
          feature_name: f.feature_name,
          value_range: valueRange
        }
      })
      
      form.setFieldsValue({
        name: record.name,
        description: record.description,
        keywords: record.keywords || [],
        status: record.status,
        features: featuresData
      })
    } else {
      form.resetFields()
      form.setFieldsValue({
        status: 'active',
        keywords: [],
        features: []
      })
    }
    setModalVisible(true)
  }

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      
      // 处理特征数据
      const featuresData = (values.features || []).map(f => {
        const feature = features.find(fe => fe.id === f.feature_id)
        let valueRange = f.value_range
        
        // 如果 value_range 是数组（多选框返回的），需要转换为 JSON 字符串
        // 如果已经是字符串，保持原样
        if (Array.isArray(valueRange)) {
          // 数组类型，转换为 JSON 字符串
          valueRange = JSON.stringify(valueRange)
        }
        // 如果 value_range 是 null 或 undefined，保持原样（后端会处理）
        
        return {
          feature_id: f.feature_id,
          feature_name: feature ? feature.name : '',
          value_type: 'enum', // 默认使用 enum 类型
          value_range: valueRange
        }
      })
      
      const data = {
        name: values.name,
        description: values.description,
        keywords: values.keywords || [],
        status: values.status,
        features: featuresData
      }

      if (editingRecord) {
        // 更新
        const response = await api.put(`/sample-sets/${editingRecord.id}`, data)
        if (response.code === 200) {
          message.success('更新成功')
          setModalVisible(false)
          fetchData(pagination.current, pagination.pageSize)
        } else {
          message.error(response.message || '更新失败')
        }
      } else {
        // 创建
        const response = await api.post('/sample-sets', data)
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
        message.error('请填写完整信息')
      } else {
        message.error('操作失败：' + (error.response?.data?.message || error.message))
      }
      console.error('提交错误:', error)
    }
  }

  // 复制样本集
  const handleCopy = async (record) => {
    try {
      const response = await api.post(`/sample-sets/${record.id}/copy`)
      if (response.code === 200) {
        message.success('样本集复制成功')
        // 自动打开编辑弹窗，让用户修改复制的样本集
        const copiedRecord = response.data
        handleOpenModal(copiedRecord)
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error(response.message || '复制样本集失败')
      }
    } catch (error) {
      message.error('复制样本集失败：' + (error.response?.data?.message || error.message))
      console.error('复制样本集错误:', error)
    }
  }

  // 删除
  const handleDelete = async (id) => {
    try {
      const response = await api.delete(`/sample-sets/${id}`)
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
      message.warning('请选择要删除的样本集')
      return
    }
    
    try {
      const response = await api.delete('/sample-sets/batch', {
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

  // 计算样本集数据
  const handleCalculate = async (record) => {
    try {
      const response = await api.post(`/sample-sets/${record.id}/calculate`)
      if (response.code === 200) {
        message.success(`计算完成，匹配到 ${response.data.matched_count || 0} 张图片`)
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error(response.message || '计算失败')
      }
    } catch (error) {
      message.error('计算失败：' + (error.response?.data?.message || error.message))
      console.error('计算错误:', error)
    }
  }

  // 打包样本集
  const handlePackage = async (record) => {
    try {
      const response = await api.post(`/sample-sets/${record.id}/package`)
      if (response.code === 200) {
        message.success('打包任务已启动，请稍候查看打包状态')
        // 轮询检查打包状态
        const checkInterval = setInterval(async () => {
          await fetchData(pagination.current, pagination.pageSize)
          const updatedRecord = dataSource.find(item => item.id === record.id)
          if (updatedRecord && updatedRecord.package_status !== 'packing') {
            clearInterval(checkInterval)
            if (updatedRecord.package_status === 'packed') {
              message.success('打包完成')
            } else if (updatedRecord.package_status === 'failed') {
              message.error('打包失败')
            }
          }
        }, 2000)
        // 30秒后停止轮询
        setTimeout(() => clearInterval(checkInterval), 30000)
      } else {
        message.error(response.message || '启动打包失败')
      }
    } catch (error) {
      message.error('启动打包失败：' + (error.response?.data?.message || error.message))
      console.error('打包错误:', error)
    }
  }

  // 下载样本集压缩包
  const handleDownload = async (record) => {
    try {
      const url = `/api/sample-sets/${record.id}/download`
      const link = document.createElement('a')
      link.href = url
      link.download = ''
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch (error) {
      message.error('下载失败：' + (error.response?.data?.message || error.message))
      console.error('下载错误:', error)
    }
  }

  // 刷新样本集状态
  const handleRefresh = async (record) => {
    try {
      const response = await api.post(`/sample-sets/${record.id}/refresh`)
      if (response.code === 200) {
        message.success('刷新成功')
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error(response.message || '刷新失败')
      }
    } catch (error) {
      message.error('刷新失败：' + (error.response?.data?.message || error.message))
      console.error('刷新错误:', error)
    }
  }

  // 查看样本集
  const handleView = (record) => {
    navigate(`/sample-set/view?sampleSetId=${record.id}`)
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
      title: '样本集名称',
      dataIndex: 'name',
      key: 'name',
      width: 200
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: 200,
      ellipsis: true,
      render: (text) => text || <span style={{ color: '#999' }}>无</span>
    },
    {
      title: '筛选特征',
      dataIndex: 'features',
      key: 'features',
      width: 250,
      render: (features) => {
        if (!features || !Array.isArray(features) || features.length === 0) {
          return <span style={{ color: '#999' }}>无</span>
        }
        return (
          <Space wrap>
            {features.slice(0, 3).map((feature, idx) => (
              <Tag key={idx} color="blue">{feature.feature_name}</Tag>
            ))}
            {features.length > 3 && <Tag>+{features.length - 3}</Tag>}
          </Space>
        )
      }
    },
    {
      title: '图片数量',
      dataIndex: 'image_count',
      key: 'image_count',
      width: 100,
      render: (count) => count || 0
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const statusMap = {
          'active': { color: 'success', text: '启用' },
          'inactive': { color: 'default', text: '禁用' }
        }
        const statusInfo = statusMap[status] || { color: 'default', text: status }
        return <Tag color={statusInfo.color}>{statusInfo.text}</Tag>
      }
    },
    {
      title: '打包状态',
      dataIndex: 'package_status',
      key: 'package_status',
      width: 120,
      render: (package_status) => {
        const statusMap = {
          'unpacked': { color: 'default', text: '未打包' },
          'packing': { color: 'processing', text: '打包中' },
          'packed': { color: 'success', text: '已打包' },
          'failed': { color: 'error', text: '打包失败' }
        }
        const statusInfo = statusMap[package_status] || { color: 'default', text: package_status }
        return <Tag color={statusInfo.color}>{statusInfo.text}</Tag>
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
      width: 300,
      fixed: 'right',
      render: (_, record) => {
        return (
          <Space size="small" wrap style={{ width: '100%', justifyContent: 'flex-start' }}>
            <Button
              type="link"
              size="small"
              icon={<CalculatorOutlined />}
              onClick={() => handleCalculate(record)}
            >
              计算数据
            </Button>
            <Button
              type="link"
              size="small"
              icon={<InboxOutlined />}
              onClick={() => handlePackage(record)}
              disabled={record.package_status === 'packing'}
            >
              打包
            </Button>
            {record.package_status === 'packed' && (
              <Button
                type="link"
                size="small"
                icon={<DownloadOutlined />}
                onClick={() => handleDownload(record)}
              >
                下载
              </Button>
            )}
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleView(record)}
            >
              查看
            </Button>
            <Button
              type="link"
              size="small"
              icon={<ReloadOutlined />}
              onClick={() => handleRefresh(record)}
            >
              刷新
            </Button>
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleOpenModal(record)}
            >
              编辑
            </Button>
            <Button
              type="link"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => handleCopy(record)}
              title="复制样本集"
            >
              复制
            </Button>
            <Popconfirm
              title="确定要删除这个样本集吗？"
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
    }
  ]

  const rowSelection = {
    selectedRowKeys,
    onChange: setSelectedRowKeys
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <Input
              placeholder="搜索样本集名称"
              prefix={<SearchOutlined />}
              style={{ width: 200 }}
              value={filters.keyword}
              onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
              allowClear
              onPressEnter={() => fetchData(1, pagination.pageSize)}
            />
            <Select
              placeholder="选择状态"
              style={{ width: 150 }}
              value={filters.status}
              onChange={(value) => setFilters({ ...filters, status: value })}
              allowClear
            >
              <Option value="active">启用</Option>
              <Option value="inactive">禁用</Option>
            </Select>
          </Space>
          <Space>
            {selectedRowKeys.length > 0 && (
              <Popconfirm
                title={`确定要删除选中的 ${selectedRowKeys.length} 个样本集吗？`}
                onConfirm={handleBatchDelete}
                okText="确定"
                cancelText="取消"
              >
                <Button danger>批量删除</Button>
              </Popconfirm>
            )}
            <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
              新建样本集
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
              fetchData(page, pageSize)
            }
          }}
          rowSelection={rowSelection}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 创建/编辑模态框 */}
      <Modal
        title={editingRecord ? '编辑样本集' : '新建样本集'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={800}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            status: 'active',
            features: []
          }}
        >
          <Form.Item
            name="name"
            label="样本集名称"
            rules={[{ required: true, message: '请输入样本集名称' }]}
          >
            <Input placeholder="请输入样本集名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={3} placeholder="请输入样本集描述" />
          </Form.Item>

          <Form.Item
            name="keywords"
            label="关键字列表"
            tooltip="选择关键字以限定图片范围，可多选"
          >
            <Select
              mode="tags"
              placeholder="选择或输入关键字，按回车添加"
              style={{ width: '100%' }}
              tokenSeparators={[',']}
              allowClear
            >
              {keywords.map(keyword => (
                <Option key={keyword} value={keyword}>{keyword}</Option>
              ))}
            </Select>
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

          <Form.Item
            name="features"
            label="筛选特征"
          >
            <Form.List name="features">
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <div key={key} style={{ marginBottom: 16, padding: 16, border: '1px solid #d9d9d9', borderRadius: 4 }}>
                      <Space direction="vertical" style={{ width: '100%' }} size="middle">
                        <Form.Item
                          {...restField}
                          name={[name, 'feature_id']}
                          label="特征"
                          rules={[{ required: true, message: '请选择特征' }]}
                        >
                          <Select 
                            placeholder="请选择特征" 
                            style={{ width: '100%' }}
                            onChange={(value) => {
                              // 当选择特征时，清空之前设置的 value_range，让用户重新选择
                              form.setFieldValue(['features', name, 'value_range'], undefined)
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
                          noStyle
                          shouldUpdate={(prevValues, currentValues) => {
                            const prevFeatureId = prevValues.features?.[name]?.feature_id
                            const currentFeatureId = currentValues.features?.[name]?.feature_id
                            return prevFeatureId !== currentFeatureId
                          }}
                        >
                          {({ getFieldValue }) => {
                            const featureId = getFieldValue(['features', name, 'feature_id'])
                            const selectedFeature = features.find(f => f.id === featureId)
                            
                            // 获取特征值列表
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
                            
                            // 如果特征有预定义的值，显示为多选框
                            if (featureValues.length > 0) {
                              return (
                                <Form.Item
                                  {...restField}
                                  name={[name, 'value_range']}
                                  label="选择特征值"
                                >
                                  <Checkbox.Group style={{ width: '100%' }}>
                                    {featureValues.map((value, idx) => (
                                      <Checkbox key={idx} value={value}>
                                        {value}
                                      </Checkbox>
                                    ))}
                                  </Checkbox.Group>
                                </Form.Item>
                              )
                            } else {
                              // 如果没有预定义值，使用标签输入框
                              return (
                                <Form.Item
                                  {...restField}
                                  name={[name, 'value_range']}
                                  label="可选值（多个值用逗号分隔）"
                                >
                                  <Select
                                    mode="tags"
                                    placeholder="输入值后按回车"
                                    style={{ width: '100%' }}
                                    tokenSeparators={[',']}
                                  />
                                </Form.Item>
                              )
                            }
                          }}
                        </Form.Item>

                        <Button type="link" danger onClick={() => remove(name)}>
                          删除特征
                        </Button>
                      </Space>
                    </div>
                  ))}
                  <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                    添加特征
                  </Button>
                </>
              )}
            </Form.List>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default SampleSetManagement

