import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
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
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, PlayCircleOutlined, EyeOutlined, RightCircleOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Option } = Select
const { TextArea } = Input

const RequirementManagement = () => {
  const navigate = useNavigate()
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
  const [cookieOptions, setCookieOptions] = useState([]) // Cookie账号列表
  const [progressModalVisible, setProgressModalVisible] = useState(false)
  const [currentRequirementId, setCurrentRequirementId] = useState(null)
  const [progressData, setProgressData] = useState(null)
  const [progressLoading, setProgressLoading] = useState(false)

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
    fetchCookies('xiaohongshu') // 默认加载小红书平台的账号
  }, [])

  // 获取Cookie列表（根据平台筛选）
  const fetchCookies = async (platform) => {
    if (!platform) {
      setCookieOptions([])
      return
    }
    try {
      const response = await api.get('/crawler/cookies', {
        params: { page: 1, page_size: 1000, platform, status: 'active' }
      })
      if (response.code === 200) {
        const cookies = response.data.list || []
        setCookieOptions(cookies.map(cookie => ({
          value: cookie.id,
          label: cookie.platform_account || `Cookie #${cookie.id}`,
          cookie: cookie
        })))
      }
    } catch (error) {
      console.error('获取Cookie列表失败:', error)
      setCookieOptions([])
    }
  }

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
        cookie_id: record.cookie_id,
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
        cookie_id: values.cookie_id || null,
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

  // 启动需求
  const handleStart = async (record) => {
    try {
      const response = await api.post(`/requirements/${record.id}/start`)
      if (response.code === 200) {
        message.success('需求启动成功')
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error(response.message || '启动失败')
      }
    } catch (error) {
      message.error('启动失败：' + (error.response?.data?.message || error.message))
      console.error('启动错误:', error)
    }
  }

  // 查看进度
  const handleViewProgress = async (record) => {
    setCurrentRequirementId(record.id)
    setProgressModalVisible(true)
    await fetchProgress(record.id)
  }

  // 获取进度
  const fetchProgress = async (requirementId) => {
    setProgressLoading(true)
    try {
      const response = await api.get(`/requirements/${requirementId}/progress`)
      if (response.code === 200) {
        setProgressData(response.data)
      } else {
        message.error(response.message || '获取进度失败')
      }
    } catch (error) {
      message.error('获取进度失败：' + (error.response?.data?.message || error.message))
    } finally {
      setProgressLoading(false)
    }
  }

  // 执行下一个任务
  const handleExecuteNext = async () => {
    if (!currentRequirementId) return
    try {
      const response = await api.post(`/requirements/${currentRequirementId}/execute-next`)
      if (response.code === 200) {
        message.success(response.message || '任务已启动')
        await fetchProgress(currentRequirementId)
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error(response.message || '执行失败')
      }
    } catch (error) {
      message.error('执行失败：' + (error.response?.data?.message || error.message))
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
          {record.status === 'pending' && (
            <Button
              type="link"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => handleStart(record)}
            >
              启动
            </Button>
          )}
          {(record.status === 'active' || record.status === 'completed') && (
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => navigate(`/requirement/progress/${record.id}`)}
            >
              进度
            </Button>
          )}
          {record.status === 'pending' && (
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleOpenModal(record)}
            >
              编辑
            </Button>
          )}
          {record.status === 'pending' && (
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
          )}
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
            name="cookie_id"
            label="抓取账号"
            tooltip="选择用于抓取的账号Cookie，如果不选择则使用该平台默认的active状态Cookie"
          >
            <Select 
              placeholder="请选择账号（可选）"
              allowClear
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
            >
              {cookieOptions.map(option => (
                <Option key={option.value} value={option.value}>
                  {option.label}
                </Option>
              ))}
            </Select>
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
            extra={
              <Button
                type="link"
                size="small"
                onClick={() => {
                  // 全选所有特征
                  const allFeatureIds = features.map(f => f.id)
                  form.setFieldsValue({ tagging_features: allFeatureIds })
                  
                  // 自动添加到样本集的特征范围
                  const newSampleSetFeatures = allFeatureIds.map(featureId => {
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
                  
                  form.setFieldsValue({
                    sample_set_features: newSampleSetFeatures
                  })
                }}
                style={{ padding: 0, height: 'auto' }}
              >
                全选
              </Button>
            }
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
                } else {
                  // 如果清空了选择，也清空样本集特征
                  form.setFieldsValue({
                    sample_set_features: []
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

      {/* 进度查看模态框 */}
      <Modal
        title="需求进度"
        open={progressModalVisible}
        onCancel={() => {
          setProgressModalVisible(false)
          setProgressData(null)
          setCurrentRequirementId(null)
        }}
        width={800}
        footer={[
          progressData?.can_execute_next && (
            <Button
              key="execute"
              type="primary"
              icon={<RightCircleOutlined />}
              onClick={handleExecuteNext}
            >
              执行下一个任务
            </Button>
          ),
          <Button key="close" onClick={() => {
            setProgressModalVisible(false)
            setProgressData(null)
            setCurrentRequirementId(null)
          }}>
            关闭
          </Button>
        ]}
      >
        {progressLoading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>加载中...</div>
        ) : progressData ? (
          <div>
            <div style={{ marginBottom: 20 }}>
              <Space>
                <span>总任务数：{progressData.total_tasks}</span>
                <span>已完成：{progressData.completed_tasks}</span>
                <span>当前任务：{progressData.current_task_order || '无'}</span>
              </Space>
            </div>
            <div>
              {progressData.tasks && progressData.tasks.map((task, index) => {
                const taskTypeMap = {
                  'crawler': '抓取任务',
                  'cleaning': '清洗任务',
                  'tagging': '打标任务',
                  'sample_set': '样本集'
                }
                const statusMap = {
                  'pending': { color: 'default', text: '待执行' },
                  'running': { color: 'processing', text: '执行中' },
                  'completed': { color: 'success', text: '已完成' },
                  'failed': { color: 'error', text: '失败' }
                }
                const statusInfo = statusMap[task.status] || { color: 'default', text: task.status }
                
                return (
                  <div
                    key={task.id}
                    style={{
                      padding: '12px',
                      marginBottom: '8px',
                      border: '1px solid #f0f0f0',
                      borderRadius: '4px',
                      backgroundColor: task.order === progressData.current_task_order ? '#e6f7ff' : '#fff'
                    }}
                  >
                    <Space>
                      <span style={{ fontWeight: 'bold' }}>步骤 {task.order}:</span>
                      <span>{taskTypeMap[task.task_type] || task.task_type}</span>
                      <Tag color={statusInfo.color}>{statusInfo.text}</Tag>
                      {task.name && <span style={{ color: '#999' }}>{task.name}</span>}
                    </Space>
                    {task.started_at && (
                      <div style={{ marginTop: 4, fontSize: 12, color: '#999' }}>
                        开始时间: {task.started_at}
                      </div>
                    )}
                    {task.finished_at && (
                      <div style={{ marginTop: 4, fontSize: 12, color: '#999' }}>
                        完成时间: {task.finished_at}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px' }}>暂无进度数据</div>
        )}
      </Modal>
    </div>
  )
}

export default RequirementManagement

