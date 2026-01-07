import React, { useState } from 'react'
import {
  Card,
  Upload,
  Button,
  Space,
  message,
  Tag,
  Descriptions,
  Spin,
  Typography,
  Radio,
  Divider
} from 'antd'
import { UploadOutlined, ReloadOutlined, FileTextOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Title, Text } = Typography
const { Dragger } = Upload

const LutAnalysisTest = () => {
  const [loading, setLoading] = useState(false)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [analysisMode, setAnalysisMode] = useState('direct') // 'direct' 或 'standard-image'

  const handleUpload = async (file) => {
    // 检查文件格式
    if (!file.name.toLowerCase().endsWith('.cube')) {
      message.error('目前只支持.cube格式的LUT文件')
      return false
    }

    setLoading(true)
    setAnalysisResult(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('mode', analysisMode)

      const response = await api.post('/lut-files/test-analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      if (response.code === 200) {
        setAnalysisResult(response.data)
        message.success('分析成功')
      } else {
        message.error(response.message || '分析失败')
      }
    } catch (error) {
      message.error('分析失败：' + (error.response?.data?.message || error.message))
      console.error('分析错误:', error)
    } finally {
      setLoading(false)
    }

    return false // 阻止自动上传
  }

  const handleReset = () => {
    setAnalysisResult(null)
  }

  const getToneColor = (tone) => {
    if (tone === '暖调') return 'orange'
    if (tone === '冷调') return 'blue'
    return 'default'
  }

  const getSaturationColor = (saturation) => {
    if (saturation === '高饱和') return 'red'
    if (saturation === '中饱和') return 'orange'
    return 'cyan'
  }

  const getContrastColor = (contrast) => {
    if (contrast === '高对比') return 'purple'
    if (contrast === '中对比') return 'blue'
    return 'default'
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Title level={3}>LUT分析测试</Title>

          {/* 分析方式选择 */}
          <div>
            <Text strong style={{ marginRight: 16 }}>分析方式：</Text>
            <Radio.Group
              value={analysisMode}
              onChange={(e) => {
                setAnalysisMode(e.target.value)
                setAnalysisResult(null)
              }}
            >
              <Radio value="direct">直接计算LUT文件</Radio>
              <Radio value="standard-image">使用标准图</Radio>
            </Radio.Group>
          </div>

          <Divider />

          {analysisMode === 'direct' && (
            <>
              {/* 文件上传区域 */}
              <Card size="small">
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  <Dragger
                    accept=".cube"
                    beforeUpload={handleUpload}
                    showUploadList={false}
                    disabled={loading}
                  >
                    <p className="ant-upload-drag-icon">
                      <FileTextOutlined style={{ fontSize: 48, color: '#1890ff' }} />
                    </p>
                    <p className="ant-upload-text">点击或拖拽LUT文件到此区域上传</p>
                    <p className="ant-upload-hint">
                      支持.cube格式的LUT文件
                    </p>
                  </Dragger>

                  <Space>
                    <Button
                      icon={<ReloadOutlined />}
                      onClick={handleReset}
                      disabled={loading || !analysisResult}
                    >
                      重置
                    </Button>
                  </Space>
                </Space>
              </Card>

              {/* 分析结果 */}
              {loading && (
                <Card>
                  <div style={{ textAlign: 'center', padding: '40px' }}>
                    <Spin size="large" />
                    <div style={{ marginTop: 16 }}>正在分析LUT文件...</div>
                  </div>
                </Card>
              )}

              {analysisResult && !loading && (
                <Card title="分析结果">
                  <Space direction="vertical" style={{ width: '100%' }} size="large">
                    <Descriptions title="文件信息" bordered column={2}>
                      <Descriptions.Item label="文件名">
                        {analysisResult.filename}
                      </Descriptions.Item>
                      <Descriptions.Item label="文件格式">
                        .cube
                      </Descriptions.Item>
                    </Descriptions>

                    <Descriptions title="标签分类" bordered column={1}>
                      <Descriptions.Item label="色调">
                        {analysisResult.analysis_result?.tone ? (
                          <Tag color={getToneColor(analysisResult.analysis_result.tone)}>
                            {analysisResult.analysis_result.tone}
                          </Tag>
                        ) : (
                          <Text type="secondary">未识别</Text>
                        )}
                      </Descriptions.Item>
                      <Descriptions.Item label="饱和度">
                        {analysisResult.analysis_result?.saturation ? (
                          <Tag color={getSaturationColor(analysisResult.analysis_result.saturation)}>
                            {analysisResult.analysis_result.saturation}
                          </Tag>
                        ) : (
                          <Text type="secondary">未识别</Text>
                        )}
                      </Descriptions.Item>
                      <Descriptions.Item label="对比度">
                        {analysisResult.analysis_result?.contrast ? (
                          <Tag color={getContrastColor(analysisResult.analysis_result.contrast)}>
                            {analysisResult.analysis_result.contrast}
                          </Tag>
                        ) : (
                          <Text type="secondary">未识别</Text>
                        )}
                      </Descriptions.Item>
                    </Descriptions>

                    <Descriptions title="详细数值" bordered column={2}>
                      <Descriptions.Item label="色调均值 (H)">
                        {analysisResult.analysis_result?.h_mean !== null && analysisResult.analysis_result?.h_mean !== undefined
                          ? Number(analysisResult.analysis_result.h_mean).toFixed(4)
                          : '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="饱和度均值 (S)">
                        {analysisResult.analysis_result?.s_mean !== null && analysisResult.analysis_result?.s_mean !== undefined
                          ? Number(analysisResult.analysis_result.s_mean).toFixed(4)
                          : '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="饱和度方差 (S_var)">
                        {analysisResult.analysis_result?.s_var !== null && analysisResult.analysis_result?.s_var !== undefined
                          ? Number(analysisResult.analysis_result.s_var).toFixed(4)
                          : '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="明度方差 (V_var)">
                        {analysisResult.analysis_result?.v_var !== null && analysisResult.analysis_result?.v_var !== undefined
                          ? Number(analysisResult.analysis_result.v_var).toFixed(4)
                          : '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="RGB对比度">
                        {analysisResult.analysis_result?.contrast_rgb !== null && analysisResult.analysis_result?.contrast_rgb !== undefined
                          ? Number(analysisResult.analysis_result.contrast_rgb).toFixed(4)
                          : '-'}
                      </Descriptions.Item>
                    </Descriptions>
                  </Space>
                </Card>
              )}
            </>
          )}

          {analysisMode === 'standard-image' && (
            <>
              {/* 文件上传区域 */}
              <Card size="small">
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  <div style={{ marginBottom: 16, padding: 12, backgroundColor: '#f0f0f0', borderRadius: 4 }}>
                    <Text type="secondary">
                      使用 standard.png 作为标准图，将LUT应用到标准图后分析结果图的特征
                    </Text>
                  </div>
                  <Dragger
                    accept=".cube"
                    beforeUpload={handleUpload}
                    showUploadList={false}
                    disabled={loading}
                  >
                    <p className="ant-upload-drag-icon">
                      <FileTextOutlined style={{ fontSize: 48, color: '#1890ff' }} />
                    </p>
                    <p className="ant-upload-text">点击或拖拽LUT文件到此区域上传</p>
                    <p className="ant-upload-hint">
                      支持.cube格式的LUT文件
                    </p>
                  </Dragger>

                  <Space>
                    <Button
                      icon={<ReloadOutlined />}
                      onClick={handleReset}
                      disabled={loading || !analysisResult}
                    >
                      重置
                    </Button>
                  </Space>
                </Space>
              </Card>

              {/* 分析结果 */}
              {loading && (
                <Card>
                  <div style={{ textAlign: 'center', padding: '40px' }}>
                    <Spin size="large" />
                    <div style={{ marginTop: 16 }}>正在应用LUT到标准图并分析...</div>
                  </div>
                </Card>
              )}

              {analysisResult && !loading && (
                <Card title="分析结果">
                  <Space direction="vertical" style={{ width: '100%' }} size="large">
                    <Descriptions title="文件信息" bordered column={2}>
                      <Descriptions.Item label="文件名">
                        {analysisResult.filename}
                      </Descriptions.Item>
                      <Descriptions.Item label="分析方式">
                        使用标准图
                      </Descriptions.Item>
                    </Descriptions>

                    <Descriptions title="标签分类" bordered column={1}>
                      <Descriptions.Item label="色调">
                        {analysisResult.analysis_result?.tone ? (
                          <Tag color={getToneColor(analysisResult.analysis_result.tone)}>
                            {analysisResult.analysis_result.tone}
                          </Tag>
                        ) : (
                          <Text type="secondary">未识别</Text>
                        )}
                      </Descriptions.Item>
                      <Descriptions.Item label="饱和度">
                        {analysisResult.analysis_result?.saturation ? (
                          <Tag color={getSaturationColor(analysisResult.analysis_result.saturation)}>
                            {analysisResult.analysis_result.saturation}
                          </Tag>
                        ) : (
                          <Text type="secondary">未识别</Text>
                        )}
                      </Descriptions.Item>
                      <Descriptions.Item label="对比度">
                        {analysisResult.analysis_result?.contrast ? (
                          <Tag color={getContrastColor(analysisResult.analysis_result.contrast)}>
                            {analysisResult.analysis_result.contrast}
                          </Tag>
                        ) : (
                          <Text type="secondary">未识别</Text>
                        )}
                      </Descriptions.Item>
                    </Descriptions>

                    <Descriptions title="详细数值" bordered column={2}>
                      <Descriptions.Item label="色调均值 (H)">
                        {analysisResult.analysis_result?.h_mean !== null && analysisResult.analysis_result?.h_mean !== undefined
                          ? Number(analysisResult.analysis_result.h_mean).toFixed(4)
                          : '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="饱和度均值 (S)">
                        {analysisResult.analysis_result?.s_mean !== null && analysisResult.analysis_result?.s_mean !== undefined
                          ? Number(analysisResult.analysis_result.s_mean).toFixed(4)
                          : '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="饱和度方差 (S_var)">
                        {analysisResult.analysis_result?.s_var !== null && analysisResult.analysis_result?.s_var !== undefined
                          ? Number(analysisResult.analysis_result.s_var).toFixed(4)
                          : '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="明度方差 (V_var)">
                        {analysisResult.analysis_result?.v_var !== null && analysisResult.analysis_result?.v_var !== undefined
                          ? Number(analysisResult.analysis_result.v_var).toFixed(4)
                          : '-'}
                      </Descriptions.Item>
                      <Descriptions.Item label="RGB对比度">
                        {analysisResult.analysis_result?.contrast_rgb !== null && analysisResult.analysis_result?.contrast_rgb !== undefined
                          ? Number(analysisResult.analysis_result.contrast_rgb).toFixed(4)
                          : '-'}
                      </Descriptions.Item>
                    </Descriptions>
                  </Space>
                </Card>
              )}
            </>
          )}
        </Space>
      </Card>
    </div>
  )
}

export default LutAnalysisTest

