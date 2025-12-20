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
  Tag
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, DownloadOutlined, EyeOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Option } = Select
const { TextArea } = Input

const CrawlerCookie = () => {
  const [dataSource, setDataSource] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  })
  const [modalVisible, setModalVisible] = useState(false)
  const [editingRecord, setEditingRecord] = useState(null)
  const [form] = Form.useForm()
  const [viewModalVisible, setViewModalVisible] = useState(false)
  const [viewingRecord, setViewingRecord] = useState(null)

  // 获取列表数据
  const fetchData = async (page = 1, pageSize = 10) => {
    setLoading(true)
    try {
      const response = await api.get('/crawler/cookies', {
        params: { page, page_size: pageSize }
      })
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
      const errorMsg = error.response?.data?.message || error.message || '未知错误'
      message.error('获取数据失败：' + errorMsg)
      console.error('API Error:', error.response?.data || error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  // 打开新增/编辑弹窗
  const handleOpenModal = async (record = null) => {
    setEditingRecord(record)
    if (record) {
      // 编辑时，先从服务器获取完整数据（包含敏感字段）
      try {
        const response = await api.get(`/crawler/cookies/${record.id}`)
        if (response.code === 200) {
          record = response.data // 使用服务器返回的完整数据
        }
      } catch (error) {
        console.error('获取Cookie详情失败:', error)
        message.warning('获取Cookie详情失败，将使用列表数据')
      }
      
      form.resetFields()
      // 先设置基础字段，触发动态字段渲染
      form.setFieldsValue({
        platform: record.platform,
        platform_account: record.platform_account,
        acquire_type: record.acquire_type,
        note: record.note
      })
      
      // 延迟设置动态字段的值，确保字段已经渲染
      setTimeout(() => {
        if (record.acquire_type === 'manual') {
          form.setFieldsValue({
            cookie_json: record.cookie_json
          })
        } else if (record.acquire_type === 'auto') {
          form.setFieldsValue({
            login_method: record.login_method
          })
          
          // 再延迟设置密码或验证码
          setTimeout(() => {
            if (record.login_method === 'password') {
              form.setFieldsValue({
                password: record.password || ''
              })
            } else if (record.login_method === 'sms') {
              form.setFieldsValue({
                verification_code: record.verification_code || ''
              })
            }
          }, 100)
        }
      }, 100)
    } else {
      form.resetFields()
      form.setFieldsValue({
        acquire_type: 'manual'
      })
    }
    setModalVisible(true)
  }

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const submitData = {
        ...values
      }
      
      // 根据获取类型清理不需要的字段
      if (submitData.acquire_type === 'manual') {
        // 手动类型：清除登录相关字段
        delete submitData.login_method
        delete submitData.password
        delete submitData.verification_code
      } else if (submitData.acquire_type === 'auto') {
        // 自动类型：清除cookie_json，根据登录方式保留对应字段
        delete submitData.cookie_json
        if (submitData.login_method === 'password') {
          delete submitData.verification_code
        } else if (submitData.login_method === 'sms') {
          delete submitData.password
        }
      }

      if (editingRecord) {
        // 更新
        const response = await api.put(`/crawler/cookies/${editingRecord.id}`, submitData)
        if (response.code === 200) {
          message.success('更新成功')
          setModalVisible(false)
          fetchData(pagination.current, pagination.pageSize)
        } else {
          message.error(response.message || '更新失败')
        }
      } else {
        // 新增
        const response = await api.post('/crawler/cookies', submitData)
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
      const response = await api.delete(`/crawler/cookies/${id}`)
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

  // 获取Cookie
  const handleFetchCookie = async (record) => {
    try {
      message.loading({ content: '正在获取Cookie，请稍候...', key: 'fetchCookie' })
      const response = await api.post(`/crawler/cookies/${record.id}/fetch`)
      if (response.code === 200) {
        message.success({ content: 'Cookie获取成功', key: 'fetchCookie' })
        fetchData(pagination.current, pagination.pageSize)
      } else {
        message.error({ content: response.message || '获取失败', key: 'fetchCookie' })
      }
    } catch (error) {
      const errorMsg = error.response?.data?.message || error.message || '未知错误'
      message.error({ content: '获取失败：' + errorMsg, key: 'fetchCookie' })
    }
  }

  // 查看Cookie详情
  const handleViewCookie = async (record) => {
    try {
      // 如果cookie_json为空，尝试从服务器获取最新数据
      if (!record.cookie_json) {
        const response = await api.get(`/crawler/cookies/${record.id}`)
        if (response.code === 200) {
          setViewingRecord(response.data)
        } else {
          setViewingRecord(record)
        }
      } else {
        setViewingRecord(record)
      }
      setViewModalVisible(true)
    } catch (error) {
      message.error('获取详情失败：' + (error.message || '未知错误'))
      setViewingRecord(record)
      setViewModalVisible(true)
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
      title: '平台',
      dataIndex: 'platform',
      key: 'platform',
      width: 120
    },
    {
      title: '平台账号',
      dataIndex: 'platform_account',
      key: 'platform_account',
      width: 150,
      ellipsis: true
    },
    {
      title: '获取类型',
      dataIndex: 'acquire_type',
      key: 'acquire_type',
      width: 100
    },
    {
      title: '登录方式',
      dataIndex: 'login_method',
      key: 'login_method',
      width: 100
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const colorMap = {
          'active': 'green',
          'inactive': 'default',
          'error': 'red'
        }
        const textMap = {
          'active': '启用',
          'inactive': '禁用',
          'error': '错误'
        }
        return <Tag color={colorMap[status] || 'default'}>{textMap[status] || status}</Tag>
      }
    },
    {
      title: '备注',
      dataIndex: 'note',
      key: 'note',
      width: 200,
      ellipsis: true
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
          {record.cookie_json && (
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewCookie(record)}
            >
              查看
            </Button>
          )}
          {record.acquire_type === 'auto' && (
            <Button
              type="link"
              size="small"
              icon={<DownloadOutlined />}
              onClick={() => handleFetchCookie(record)}
              disabled={!record.platform_account || !record.login_method}
            >
              获取
            </Button>
          )}
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

  return (
    <div>
      <Card
        title="Cookie管理"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleOpenModal()}
          >
            新增Cookie
          </Button>
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
        title={editingRecord ? '编辑Cookie' : '新增Cookie'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => {
          setModalVisible(false)
          form.resetFields()
        }}
        width={800}
        okText="确定"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            acquire_type: 'manual'
          }}
        >
          <Form.Item
            name="platform"
            label="平台"
            rules={[{ required: true, message: '请选择平台' }]}
          >
            <Select placeholder="请选择平台">
              <Option value="xiaohongshu">小红书</Option>
              <Option value="douyin">抖音</Option>
              <Option value="weibo">微博</Option>
              <Option value="other">其他</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="platform_account"
            label="平台账号"
          >
            <Input placeholder="请输入平台账号（可选）" />
          </Form.Item>

          <Form.Item
            name="acquire_type"
            label="获取类型"
            rules={[{ required: true, message: '请选择获取类型' }]}
          >
            <Select placeholder="请选择获取类型">
              <Option value="manual">手动</Option>
              <Option value="auto">自动</Option>
            </Select>
          </Form.Item>

          {/* 手动获取类型：显示Cookie JSON */}
          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues.acquire_type !== currentValues.acquire_type
            }
          >
            {({ getFieldValue }) => {
              const acquireType = getFieldValue('acquire_type')
              if (acquireType === 'manual') {
                return (
                  <Form.Item
                    name="cookie_json"
                    label="Cookie JSON值"
                    rules={[{ required: true, message: '请输入Cookie JSON值' }]}
                  >
                    <TextArea
                      rows={6}
                      placeholder="请输入Cookie JSON值"
                    />
                  </Form.Item>
                )
              }
              return null
            }}
          </Form.Item>

          {/* 自动获取类型：显示登录方式 */}
          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues.acquire_type !== currentValues.acquire_type
            }
          >
            {({ getFieldValue }) => {
              const acquireType = getFieldValue('acquire_type')
              if (acquireType === 'auto') {
                return (
                  <>
                    <Form.Item
                      name="login_method"
                      label="登录方式"
                      rules={[{ required: true, message: '请选择登录方式' }]}
                    >
                      <Select placeholder="请选择登录方式">
                        <Option value="password">密码</Option>
                        <Option value="sms">验证码</Option>
                      </Select>
                    </Form.Item>

                    {/* 密码登录方式：显示密码框 */}
                    <Form.Item
                      noStyle
                      shouldUpdate={(prevValues, currentValues) =>
                        prevValues.login_method !== currentValues.login_method
                      }
                    >
                      {({ getFieldValue }) => {
                        const loginMethod = getFieldValue('login_method')
                        if (loginMethod === 'password') {
                          return (
                            <Form.Item
                              name="password"
                              label="密码"
                              rules={[{ required: true, message: '请输入密码' }]}
                            >
                              <Input.Password placeholder="请输入密码" />
                            </Form.Item>
                          )
                        }
                        return null
                      }}
                    </Form.Item>

                    {/* 验证码登录方式：显示验证码输入框 */}
                    <Form.Item
                      noStyle
                      shouldUpdate={(prevValues, currentValues) =>
                        prevValues.login_method !== currentValues.login_method
                      }
                    >
                      {({ getFieldValue }) => {
                        const loginMethod = getFieldValue('login_method')
                        if (loginMethod === 'sms') {
                          return (
                            <Form.Item
                              name="verification_code"
                              label="验证码"
                              rules={[{ required: true, message: '请输入验证码' }]}
                            >
                              <Input placeholder="请输入验证码" />
                            </Form.Item>
                          )
                        }
                        return null
                      }}
                    </Form.Item>
                  </>
                )
              }
              return null
            }}
          </Form.Item>

          <Form.Item
            name="note"
            label="备注"
          >
            <TextArea
              rows={2}
              placeholder="请输入备注（可选）"
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 查看Cookie详情Modal */}
      <Modal
        title="Cookie详情"
        open={viewModalVisible}
        onCancel={() => {
          setViewModalVisible(false)
          setViewingRecord(null)
        }}
        width={900}
        footer={[
          <Button key="close" onClick={() => {
            setViewModalVisible(false)
            setViewingRecord(null)
          }}>
            关闭
          </Button>
        ]}
      >
        {viewingRecord && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <strong>基本信息：</strong>
              <div style={{ marginTop: 8, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
                <div><strong>ID:</strong> {viewingRecord.id}</div>
                <div><strong>平台:</strong> {viewingRecord.platform}</div>
                <div><strong>平台账号:</strong> {viewingRecord.platform_account || '-'}</div>
                <div><strong>获取类型:</strong> {viewingRecord.acquire_type === 'manual' ? '手动' : '自动'}</div>
                <div><strong>登录方式:</strong> {viewingRecord.login_method === 'password' ? '密码' : viewingRecord.login_method === 'sms' ? '验证码' : viewingRecord.login_method || '-'}</div>
                <div><strong>状态:</strong> 
                  <span style={{ 
                    color: viewingRecord.status === 'active' ? '#52c41a' : viewingRecord.status === 'error' ? '#ff4d4f' : '#999',
                    marginLeft: 8
                  }}>
                    {viewingRecord.status === 'active' ? '启用' : viewingRecord.status === 'error' ? '错误' : '禁用'}
                  </span>
                </div>
                {viewingRecord.note && <div><strong>备注:</strong> {viewingRecord.note}</div>}
                {viewingRecord.last_error && (
                  <div style={{ color: '#ff4d4f' }}>
                    <strong>最后错误:</strong> {viewingRecord.last_error}
                  </div>
                )}
                <div><strong>创建时间:</strong> {viewingRecord.created_at}</div>
                <div><strong>更新时间:</strong> {viewingRecord.updated_at}</div>
                {viewingRecord.fetched_at && <div><strong>抓取时间:</strong> {viewingRecord.fetched_at}</div>}
              </div>
            </div>

            <div>
              <strong>Cookie JSON：</strong>
              <div style={{ marginTop: 8 }}>
                {viewingRecord.cookie_json ? (
                  <pre style={{
                    padding: 16,
                    background: '#f5f5f5',
                    borderRadius: 4,
                    maxHeight: 500,
                    overflow: 'auto',
                    fontSize: 12,
                    lineHeight: 1.6,
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word'
                  }}>
                    {(() => {
                      try {
                        const jsonObj = JSON.parse(viewingRecord.cookie_json)
                        return JSON.stringify(jsonObj, null, 2)
                      } catch {
                        return viewingRecord.cookie_json
                      }
                    })()}
                  </pre>
                ) : (
                  <div style={{ padding: 16, background: '#f5f5f5', borderRadius: 4, color: '#999' }}>
                    暂无Cookie数据
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default CrawlerCookie
