import React, { useState, useEffect } from 'react'
import { Card, Form, Input, Button, message, Space, Alert, Tabs } from 'antd'
import { FolderOutlined, SaveOutlined } from '@ant-design/icons'
import api from '../services/api'

const { TabPane } = Tabs

const SettingsDirectory = () => {
  const [form] = Form.useForm()
  const [packageForm] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [packageLoading, setPackageLoading] = useState(false)
  const [fetching, setFetching] = useState(true)
  const [packageFetching, setPackageFetching] = useState(true)
  const [directoryInfo, setDirectoryInfo] = useState(null)
  const [packageInfo, setPackageInfo] = useState(null)

  useEffect(() => {
    fetchDirectorySettings()
    fetchPackageSettings()
  }, [])

  const fetchDirectorySettings = async () => {
    setFetching(true)
    try {
      const response = await api.get('/settings/directory')
      if (response.code === 200) {
        const data = response.data
        setDirectoryInfo(data)
        form.setFieldsValue({
          local_image_dir: data.local_image_dir
        })
      } else {
        message.error(response.message || '获取目录设置失败')
      }
    } catch (error) {
      message.error('获取目录设置失败：' + (error.response?.data?.message || error.message))
      console.error('获取目录设置错误:', error)
    } finally {
      setFetching(false)
    }
  }

  const fetchPackageSettings = async () => {
    setPackageFetching(true)
    try {
      const response = await api.get('/settings/package-directory')
      if (response.code === 200) {
        const data = response.data
        setPackageInfo(data)
        packageForm.setFieldsValue({
          package_storage_dir: data.package_storage_dir
        })
      } else {
        message.error(response.message || '获取打包目录设置失败')
      }
    } catch (error) {
      message.error('获取打包目录设置失败：' + (error.response?.data?.message || error.message))
      console.error('获取打包目录设置错误:', error)
    } finally {
      setPackageFetching(false)
    }
  }

  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)
      
      const response = await api.put('/settings/directory', {
        local_image_dir: values.local_image_dir
      })
      
      if (response.code === 200) {
        message.success('目录设置保存成功')
        // 更新目录信息
        setDirectoryInfo(response.data)
      } else {
        message.error(response.message || '保存失败')
      }
    } catch (error) {
      if (error.response?.status === 400) {
        message.error(error.response?.data?.message || '目录路径格式错误')
      } else {
        message.error('保存失败：' + (error.response?.data?.message || error.message))
      }
      console.error('保存目录设置错误:', error)
    } finally {
      setLoading(false)
    }
  }

  const handlePackageSave = async () => {
    try {
      const values = await packageForm.validateFields()
      setPackageLoading(true)
      
      const response = await api.put('/settings/package-directory', {
        package_storage_dir: values.package_storage_dir
      })
      
      if (response.code === 200) {
        message.success('打包目录设置保存成功')
        // 更新目录信息
        setPackageInfo(response.data)
      } else {
        message.error(response.message || '保存失败')
      }
    } catch (error) {
      if (error.response?.status === 400) {
        message.error(error.response?.data?.message || '目录路径格式错误')
      } else {
        message.error('保存失败：' + (error.response?.data?.message || error.message))
      }
      console.error('保存打包目录设置错误:', error)
    } finally {
      setPackageLoading(false)
    }
  }

  return (
    <div>
      <Card
        title={
          <Space>
            <FolderOutlined />
            <span>目录设置</span>
          </Space>
        }
      >
        <Tabs defaultActiveKey="image">
          <TabPane tab="图片存储目录" key="image">
        <Alert
          message="说明"
          description={
            <div>
              <p>设置本地图片保存目录。用户下载的图片将保存在此目录下。</p>
              <p>在数据库中存储的是相对路径，实际文件保存在此目录下。</p>
              <p>支持相对路径（如：./storage/images）或绝对路径（如：D:/images）。</p>
            </div>
          }
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
        >
          <Form.Item
            name="local_image_dir"
            label="本地图片存储目录"
            rules={[
              { required: true, message: '请输入目录路径' },
              {
                validator: (_, value) => {
                  if (!value || value.trim() === '') {
                    return Promise.reject(new Error('目录路径不能为空'))
                  }
                  return Promise.resolve()
                }
              }
            ]}
            help="支持相对路径（如：./storage/images）或绝对路径（如：D:/images）"
          >
            <Input
              placeholder="请输入目录路径，如：./storage/images"
              prefix={<FolderOutlined />}
            />
          </Form.Item>

          {directoryInfo && (
            <Form.Item label="当前配置信息">
              <div style={{ 
                padding: '12px', 
                background: '#f5f5f5', 
                borderRadius: '4px',
                fontSize: '13px'
              }}>
                <div style={{ marginBottom: '8px' }}>
                  <strong>用户设置路径：</strong>
                  <code style={{ 
                    marginLeft: '8px', 
                    padding: '2px 6px', 
                    background: '#fff',
                    borderRadius: '2px'
                  }}>
                    {directoryInfo.local_image_dir}
                  </code>
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <strong>解析后绝对路径：</strong>
                  <code style={{ 
                    marginLeft: '8px', 
                    padding: '2px 6px', 
                    background: '#fff',
                    borderRadius: '2px'
                  }}>
                    {directoryInfo.absolute_path}
                  </code>
                </div>
                <div>
                  <strong>目录状态：</strong>
                  <span style={{ 
                    marginLeft: '8px',
                    color: directoryInfo.exists ? '#52c41a' : '#ff4d4f'
                  }}>
                    {directoryInfo.exists ? '✓ 目录存在' : '✗ 目录不存在（保存时将自动创建）'}
                  </span>
                </div>
              </div>
            </Form.Item>
          )}

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<SaveOutlined />}
              loading={loading}
            >
              保存设置
            </Button>
          </Form.Item>
        </Form>
          </TabPane>
          <TabPane tab="打包存储目录" key="package">
            <Alert
              message="说明"
              description={
                <div>
                  <p>设置样本集打包文件的存储目录。打包后的压缩包将保存在此目录下。</p>
                  <p>支持相对路径（如：./storage/packages）或绝对路径（如：D:/packages）。</p>
                </div>
              }
              type="info"
              showIcon
              style={{ marginBottom: 24 }}
            />

            <Form
              form={packageForm}
              layout="vertical"
              onFinish={handlePackageSave}
            >
              <Form.Item
                name="package_storage_dir"
                label="打包存储目录"
                rules={[
                  { required: true, message: '请输入目录路径' },
                  {
                    validator: (_, value) => {
                      if (!value || value.trim() === '') {
                        return Promise.reject(new Error('目录路径不能为空'))
                      }
                      return Promise.resolve()
                    }
                  }
                ]}
                help="支持相对路径（如：./storage/packages）或绝对路径（如：D:/packages）"
              >
                <Input
                  placeholder="请输入目录路径，如：./storage/packages"
                  prefix={<FolderOutlined />}
                />
              </Form.Item>

              {packageInfo && (
                <Form.Item label="当前配置信息">
                  <div style={{ 
                    padding: '12px', 
                    background: '#f5f5f5', 
                    borderRadius: '4px',
                    fontSize: '13px'
                  }}>
                    <div style={{ marginBottom: '8px' }}>
                      <strong>用户设置路径：</strong>
                      <code style={{ 
                        marginLeft: '8px', 
                        padding: '2px 6px', 
                        background: '#fff',
                        borderRadius: '2px'
                      }}>
                        {packageInfo.package_storage_dir}
                      </code>
                    </div>
                    <div style={{ marginBottom: '8px' }}>
                      <strong>解析后绝对路径：</strong>
                      <code style={{ 
                        marginLeft: '8px', 
                        padding: '2px 6px', 
                        background: '#fff',
                        borderRadius: '2px'
                      }}>
                        {packageInfo.absolute_path}
                      </code>
                    </div>
                    <div>
                      <strong>目录状态：</strong>
                      <span style={{ 
                        marginLeft: '8px',
                        color: packageInfo.exists ? '#52c41a' : '#ff4d4f'
                      }}>
                        {packageInfo.exists ? '✓ 目录存在' : '✗ 目录不存在（保存时将自动创建）'}
                      </span>
                    </div>
                  </div>
                </Form.Item>
              )}

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  icon={<SaveOutlined />}
                  loading={packageLoading}
                >
                  保存设置
                </Button>
              </Form.Item>
            </Form>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default SettingsDirectory

