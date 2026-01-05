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
  Drawer,
  Checkbox,
  Row,
  Col,
  Statistic,
  Progress
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, EyeOutlined, CalculatorOutlined, CheckCircleOutlined, StarOutlined, ReloadOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

const { Option } = Select
const { TextArea } = Input

const StyleManagement = () => {
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
  const [sampleSets, setSampleSets] = useState([])
  const [profileDrawerVisible, setProfileDrawerVisible] = useState(false)
  const [currentStyleId, setCurrentStyleId] = useState(null)
  const [featureProfiles, setFeatureProfiles] = useState([])
  const [loadingProfiles, setLoadingProfiles] = useState(false)
  const [selectedProfileIds, setSelectedProfileIds] = useState([])
  const [aestheticModalVisible, setAestheticModalVisible] = useState(false)
  const [currentAestheticStyleId, setCurrentAestheticStyleId] = useState(null)
  const [evaluatorType, setEvaluatorType] = useState('artimuse')
  const [scoreMode, setScoreMode] = useState('score_and_reason') // score_only: 仅评分, score_and_reason: 评分和理由

  // 获取样本集列表
  const fetchSampleSets = async () => {
    try {
      const response = await api.get('/sample-sets', { params: { page: 1, page_size: 1000, status: 'active' } })
      if (response.code === 200) {
        setSampleSets(response.data.list || [])
      }
    } catch (error) {
      console.error('获取样本集列表失败:', error)
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
      
      const response = await api.get('/styles', { params })
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
    fetchSampleSets()
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
        sample_set_id: record.sample_set_id,
        status: record.status
      })
    } else {
      form.resetFields()
      form.setFieldsValue({
        status: 'active'
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
        const response = await api.put(`/styles/${editingRecord.id}`, values)
        if (response.code === 200) {
          message.success('更新成功')
          setModalVisible(false)
          fetchData(pagination.current, pagination.pageSize)
        } else {
          message.error(response.message || '更新失败')
        }
      } else {
        // 新增
        const response = await api.post('/styles', values)
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
      const response = await api.delete(`/styles/${id}`)
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

  // 查看图片
  const handleViewImages = (record) => {
    navigate(`/style/view?styleId=${record.id}`)
  }

  // 计算特征分布
  const handleCalculateDistribution = async (record) => {
    try {
      const response = await api.post(`/styles/${record.id}/calculate-feature-distribution`)
      if (response.code === 200) {
        message.success('特征分布计算完成')
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error(response.message || '计算失败')
      }
    } catch (error) {
      message.error('计算失败：' + (error.response?.data?.message || error.message))
      console.error('计算错误:', error)
    }
  }

  // 打开特征画像抽屉
  const handleOpenProfileDrawer = async (record) => {
    setCurrentStyleId(record.id)
    setProfileDrawerVisible(true)
    await fetchFeatureProfiles(record.id)
  }

  // 获取特征画像列表
  const fetchFeatureProfiles = async (styleId) => {
    setLoadingProfiles(true)
    try {
      const response = await api.get(`/styles/${styleId}/feature-profiles`)
      if (response.code === 200) {
        const profiles = response.data || []
        setFeatureProfiles(profiles)
        setSelectedProfileIds(profiles.filter(p => p.is_selected).map(p => p.id))
      } else {
        message.error(response.message || '获取特征画像失败')
      }
    } catch (error) {
      message.error('获取特征画像失败：' + (error.response?.data?.message || error.message))
      console.error('获取特征画像错误:', error)
    } finally {
      setLoadingProfiles(false)
    }
  }

  // 保存特征画像选择
  const handleSaveProfileSelection = async () => {
    try {
      const response = await api.put(`/styles/${currentStyleId}/feature-profiles/batch-update`, {
        selected_ids: selectedProfileIds
      })
      if (response.code === 200) {
        message.success('特征画像保存成功')
        setProfileDrawerVisible(false)
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error(response.message || '保存失败')
      }
    } catch (error) {
      message.error('保存失败：' + (error.response?.data?.message || error.message))
      console.error('保存错误:', error)
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
      title: '风格名称',
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
      title: '关联样本集',
      dataIndex: 'sample_set_id',
      key: 'sample_set_id',
      width: 150,
      render: (sampleSetId) => {
        if (!sampleSetId) return <span style={{ color: '#999' }}>无</span>
        const sampleSet = sampleSets.find(s => s.id === sampleSetId)
        return sampleSet ? sampleSet.name : `ID: ${sampleSetId}`
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
      title: '美学评分进度',
      key: 'aesthetic_progress',
      width: 150,
      render: (_, record) => {
        const total = record.total_image_count || 0
        const processed = record.processed_image_count || 0
        const percent = total > 0 ? Math.round((processed / total) * 100) : 0
        return (
          <div>
            <div style={{ fontSize: 12, marginBottom: 4 }}>
              {processed} / {total}
            </div>
            <Progress 
              percent={percent} 
              size="small"
              status={processed === total && total > 0 ? 'success' : 'active'}
            />
          </div>
        )
      }
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
        <Space size="small" wrap style={{ width: '100%', justifyContent: 'flex-start' }}>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewImages(record)}
          >
            查看图片
          </Button>
          <Button
            type="link"
            size="small"
            icon={<CalculatorOutlined />}
            onClick={() => handleCalculateDistribution(record)}
          >
            计算分布
          </Button>
          <Button
            type="link"
            size="small"
            icon={<CheckCircleOutlined />}
            onClick={() => handleOpenProfileDrawer(record)}
          >
            特征画像
          </Button>
          <Button
            type="link"
            size="small"
            icon={<StarOutlined />}
            onClick={() => {
              setCurrentAestheticStyleId(record.id)
              setAestheticModalVisible(true)
            }}
          >
            美学评分
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
            title="确定要删除这个风格吗？"
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
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <Input
              placeholder="搜索风格名称或描述"
              prefix={<SearchOutlined />}
              style={{ width: 250 }}
              value={filters.keyword}
              onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
              allowClear
              onPressEnter={() => fetchData(1, pagination.pageSize)}
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
          </Space>
          <Space>
            {selectedRowKeys.length > 0 && (
              <Popconfirm
                title={`确定要删除选中的 ${selectedRowKeys.length} 个风格吗？`}
                onConfirm={async () => {
                  for (const id of selectedRowKeys) {
                    await handleDelete(id)
                  }
                  setSelectedRowKeys([])
                }}
                okText="确定"
                cancelText="取消"
              >
                <Button danger>批量删除</Button>
              </Popconfirm>
            )}
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => fetchData(pagination.current, pagination.pageSize)}
              loading={loading}
            >
              刷新
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
              新建风格
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
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 新增/编辑弹窗 */}
      <Modal
        title={editingRecord ? '编辑风格' : '新建风格'}
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
            status: 'active'
          }}
        >
          <Form.Item
            name="name"
            label="风格名称"
            rules={[{ required: true, message: '请输入风格名称' }]}
          >
            <Input placeholder="请输入风格名称" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={3} placeholder="请输入风格描述" />
          </Form.Item>

          <Form.Item
            name="sample_set_id"
            label="关联样本集"
            tooltip="选择样本集后，会自动从样本集导入图片"
          >
            <Select
              placeholder="请选择样本集（可选）"
              allowClear
            >
              {sampleSets.map(sampleSet => (
                <Option key={sampleSet.id} value={sampleSet.id}>
                  {sampleSet.name} ({sampleSet.image_count} 张图片)
                </Option>
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
        </Form>
      </Modal>

      {/* 特征画像抽屉 */}
      <Drawer
        title="特征画像管理"
        open={profileDrawerVisible}
        onClose={() => setProfileDrawerVisible(false)}
        width={800}
        extra={
          <Space>
            <Button onClick={() => setProfileDrawerVisible(false)}>取消</Button>
            <Button type="primary" onClick={handleSaveProfileSelection}>
              保存选择
            </Button>
          </Space>
        }
      >
        {loadingProfiles ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>加载中...</div>
        ) : (
          <div>
            <div style={{ marginBottom: 16 }}>
              <Space>
                <span>已选择: {selectedProfileIds.length} / {featureProfiles.length}</span>
                <Button
                  size="small"
                  onClick={() => {
                    setSelectedProfileIds(featureProfiles.map(p => p.id))
                  }}
                >
                  全选
                </Button>
                <Button
                  size="small"
                  onClick={() => {
                    setSelectedProfileIds([])
                  }}
                >
                  全不选
                </Button>
              </Space>
            </div>
            <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
              {featureProfiles.length > 0 ? (
                <Row gutter={[16, 16]}>
                  {featureProfiles.map(profile => {
                    // 计算总数
                    const total = profile.distribution ? profile.distribution.reduce((sum, item) => sum + item.count, 0) : 0
                    const isSelected = selectedProfileIds.includes(profile.id)
                    
                    return (
                      <Col key={profile.id} xs={24} sm={12} lg={8} xl={6}>
                        <Card 
                          size="small" 
                          title={
                            <Checkbox
                              checked={isSelected}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedProfileIds([...selectedProfileIds, profile.id])
                                } else {
                                  setSelectedProfileIds(selectedProfileIds.filter(id => id !== profile.id))
                                }
                              }}
                            >
                              {profile.feature_name}
                            </Checkbox>
                          }
                          style={{ 
                            height: '100%',
                            border: isSelected ? '2px solid #1890ff' : '1px solid #f0f0f0',
                            backgroundColor: isSelected ? '#e6f7ff' : '#fff',
                            transition: 'all 0.3s ease'
                          }}
                        >
                          {profile.distribution && profile.distribution.length > 0 ? (
                            <div>
                              {profile.distribution.slice(0, 5).map((item, itemIdx) => {
                                // 优先使用后端返回的percentage，如果没有则自己计算
                                const percentage = item.percentage !== undefined 
                                  ? item.percentage 
                                  : (total > 0 ? Math.round((item.count / total) * 100) : 0)
                                return (
                                  <div key={itemIdx} style={{ marginBottom: 12 }}>
                                    <div style={{ 
                                      display: 'flex', 
                                      justifyContent: 'space-between', 
                                      marginBottom: 4,
                                      fontSize: 12
                                    }}>
                                      <span style={{ 
                                        overflow: 'hidden',
                                        textOverflow: 'ellipsis',
                                        whiteSpace: 'nowrap',
                                        flex: 1,
                                        marginRight: 8
                                      }}>
                                        {item.value}
                                      </span>
                                      <span style={{ color: '#666', minWidth: 60, textAlign: 'right' }}>
                                        {item.count} ({percentage.toFixed(2)}%)
                                      </span>
                                    </div>
                                    <Progress 
                                      percent={percentage} 
                                      size="small"
                                      strokeColor={{
                                        '0%': '#108ee9',
                                        '100%': '#87d068',
                                      }}
                                    />
                                  </div>
                                )
                              })}
                              {profile.distribution.length > 5 && (
                                <div style={{ fontSize: 12, color: '#999', marginTop: 8, textAlign: 'center' }}>
                                  还有 {profile.distribution.length - 5} 个值...
                                </div>
                              )}
                            </div>
                          ) : (
                            <div style={{ color: '#999', fontSize: 12, textAlign: 'center' }}>
                              暂无数据
                            </div>
                          )}
                        </Card>
                      </Col>
                    )
                  })}
                </Row>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                  暂无特征画像数据，请先计算特征分布
                </div>
              )}
            </div>
          </div>
        )}
      </Drawer>

      {/* 美学评分弹窗 */}
      <Modal
        title="美学评分"
        open={aestheticModalVisible}
        onOk={async () => {
          if (!currentAestheticStyleId) return
          
          try {
            const response = await api.post(`/styles/${currentAestheticStyleId}/aesthetic-score`, {
              evaluator_type: evaluatorType,
              score_mode: scoreMode
            })
            if (response.code === 200) {
              message.success('美学评分任务已启动')
              setAestheticModalVisible(false)
              fetchData(pagination.current, pagination.pageSize)
            } else {
              message.error(response.message || '启动失败')
            }
          } catch (error) {
            message.error('启动失败：' + (error.response?.data?.message || error.message))
            console.error('启动错误:', error)
          }
        }}
        onCancel={() => setAestheticModalVisible(false)}
        okText="开始评分"
        cancelText="取消"
      >
        <Form layout="vertical">
          <Form.Item label="评分器类型">
            <Select
              value={evaluatorType}
              onChange={setEvaluatorType}
            >
              <Option value="artimuse">ArtiMuse</Option>
              <Option value="q_insight" disabled>Q-Insight（暂未实现）</Option>
            </Select>
          </Form.Item>
          {evaluatorType === 'artimuse' && (
            <Form.Item label="评分模式">
              <Select
                value={scoreMode}
                onChange={setScoreMode}
              >
                <Option value="score_only">仅评分</Option>
                <Option value="score_and_reason">评分和理由</Option>
              </Select>
            </Form.Item>
          )}
          <div style={{ color: '#999', fontSize: 12 }}>
            {evaluatorType === 'artimuse' && scoreMode === 'score_only' && '使用ArtiMuse仅对图片进行美学评分（不包含详细理由）'}
            {evaluatorType === 'artimuse' && scoreMode === 'score_and_reason' && '使用ArtiMuse对图片进行美学评分，包含详细理由'}
            {evaluatorType === 'q_insight' && 'Q-Insight功能暂未实现'}
          </div>
        </Form>
      </Modal>
    </div>
  )
}

export default StyleManagement

