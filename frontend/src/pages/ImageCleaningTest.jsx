import React, { useState, useEffect, useRef } from 'react'
import {
  Card,
  Upload,
  Button,
  Space,
  message,
  Tag,
  Descriptions,
  Image,
  Spin,
  Typography
} from 'antd'
import { UploadOutlined, ReloadOutlined } from '@ant-design/icons'
import api from '../services/api'
const { Title, Text } = Typography

// 标注图片组件
const AnnotatedImage = ({ imageUrl, faceLocations, textLocations }) => {
  const canvasRef = useRef(null)
  const imgRef = useRef(null)

  useEffect(() => {
    if (!imageUrl || !canvasRef.current) return

    const img = new window.Image()
    img.crossOrigin = 'anonymous'
    
    img.onload = () => {
      const canvas = canvasRef.current
      const ctx = canvas.getContext('2d')
      
      // 设置Canvas尺寸与图片一致
      canvas.width = img.width
      canvas.height = img.height
      
      // 绘制图片
      ctx.drawImage(img, 0, 0)
      
      // 绘制人脸方框（红色）
      if (faceLocations && faceLocations.length > 0) {
        ctx.strokeStyle = '#ff0000'
        ctx.lineWidth = 3
        ctx.font = 'bold 16px Arial'
        ctx.fillStyle = '#ff0000'
        
        faceLocations.forEach((loc, idx) => {
          const [x, y, w, h] = loc
          // 绘制方框
          ctx.strokeRect(x, y, w, h)
          // 绘制标签背景
          const text = `人脸${idx + 1}`
          const textMetrics = ctx.measureText(text)
          ctx.fillStyle = 'rgba(255, 0, 0, 0.7)'
          ctx.fillRect(x, y - 20, textMetrics.width + 10, 20)
          // 绘制标签文字
          ctx.fillStyle = '#ffffff'
          ctx.fillText(text, x + 5, y - 5)
        })
      }
      
      // 绘制文字方框（蓝色）
      if (textLocations && textLocations.length > 0) {
        ctx.strokeStyle = '#0066ff'
        ctx.lineWidth = 2
        ctx.font = 'bold 14px Arial'
        ctx.fillStyle = '#0066ff'
        
        textLocations.forEach((loc, idx) => {
          const [x, y, w, h] = loc
          // 绘制方框
          ctx.strokeRect(x, y, w, h)
          // 绘制标签（只在第一个文字区域显示）
          if (idx === 0) {
            const text = '文字区域'
            const textMetrics = ctx.measureText(text)
            ctx.fillStyle = 'rgba(0, 102, 255, 0.7)'
            ctx.fillRect(x, y - 18, textMetrics.width + 10, 18)
            ctx.fillStyle = '#ffffff'
            ctx.fillText(text, x + 5, y - 3)
          }
        })
      }
    }
    
    img.src = imageUrl
  }, [imageUrl, faceLocations, textLocations])

  return (
    <div style={{ textAlign: 'center', position: 'relative', display: 'inline-block', width: '100%' }}>
      <img
        ref={imgRef}
        src={imageUrl}
        alt="原图"
        style={{ maxWidth: '100%', maxHeight: '600px', display: 'none' }}
      />
      <canvas
        ref={canvasRef}
        style={{
          maxWidth: '100%',
          maxHeight: '600px',
          display: 'block',
          margin: '0 auto'
        }}
      />
    </div>
  )
}

const ImageCleaningTest = () => {
  const [fileList, setFileList] = useState([])
  const [loading, setLoading] = useState(false)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [imageUrl, setImageUrl] = useState('')
  const canvasRef = useRef(null)
  const imageRef = useRef(null)

  // 上传配置
  const uploadProps = {
    beforeUpload: (file) => {
      // 检查文件类型
      const isImage = file.type.startsWith('image/')
      if (!isImage) {
        message.error('只能上传图片文件！')
        return false
      }
      
      // 检查文件大小（限制10MB）
      const isLt10M = file.size / 1024 / 1024 < 10
      if (!isLt10M) {
        message.error('图片大小不能超过10MB！')
        return false
      }
      
      // 读取文件预览
      const reader = new FileReader()
      reader.onload = (e) => {
        setImageUrl(e.target && e.target.result ? e.target.result : '')
      }
      reader.readAsDataURL(file)
      
      setFileList([file])
      return false // 阻止自动上传
    },
    fileList,
    onRemove: () => {
      setFileList([])
      setImageUrl('')
      setAnalysisResult(null)
    },
    maxCount: 1
  }

  // 分析图片
  const handleAnalyze = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择图片文件')
      return
    }

    setLoading(true)
    try {
      const file = fileList[0].originFileObj || fileList[0]
      const formData = new FormData()
      formData.append('file', file)
      formData.append('filter_features', 'no_face,multiple_faces,no_person,multiple_persons,contains_text,blurry')

      const response = await api.post('/image-cleaning-test/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      if (response.code === 200) {
        setAnalysisResult(response.data)
        message.success('分析完成')
      } else {
        message.error(response.message || '分析失败')
      }
    } catch (error) {
      message.error('分析失败：' + (error.response?.data?.message || error.message))
      console.error('分析错误:', error)
    } finally {
      setLoading(false)
    }
  }

  // 重置
  const handleReset = () => {
    setFileList([])
    setImageUrl('')
    setAnalysisResult(null)
  }

  // 特征映射
  const featureMap = {
    'no_face': { color: 'red', text: '无人脸' },
    'multiple_faces': { color: 'orange', text: '多人脸' },
    'no_person': { color: 'red', text: '无人物' },
    'multiple_persons': { color: 'orange', text: '多人物' },
    'contains_text': { color: 'blue', text: '包含文字' },
    'blurry': { color: 'purple', text: '图片模糊' }
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Title level={4}>图片清洗测试</Title>
        <Text type="secondary">上传图片进行特征检测，包括人脸检测、文字检测、模糊度检测等</Text>
        
        <div style={{ marginTop: 24 }}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {/* 上传区域 */}
            <Card size="small">
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <Upload {...uploadProps}>
                  <Button icon={<UploadOutlined />}>选择图片</Button>
                </Upload>
                
                {imageUrl && (
                  <div style={{ marginTop: 16 }}>
                    <Image
                      src={imageUrl}
                      alt="预览"
                      style={{ maxWidth: '100%', maxHeight: '400px' }}
                      preview={true}
                    />
                  </div>
                )}
                
                <Space>
                  <Button
                    type="primary"
                    onClick={handleAnalyze}
                    loading={loading}
                    disabled={fileList.length === 0}
                  >
                    开始分析
                  </Button>
                  <Button
                    icon={<ReloadOutlined />}
                    onClick={handleReset}
                    disabled={fileList.length === 0 && !analysisResult}
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
                  <div style={{ marginTop: 16 }}>正在分析图片...</div>
                </div>
              </Card>
            )}

            {analysisResult && !loading && (
              <Card title="分析结果">
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                  {/* 匹配的特征 */}
                  <div>
                    <Text strong>检测到的特征：</Text>
                    <div style={{ marginTop: 8 }}>
                      {analysisResult.matched_features_cn && analysisResult.matched_features_cn.length > 0 ? (
                        <Space wrap>
                          {analysisResult.matched_features_cn.map((feature, index) => {
                            const featureKey = Object.keys(featureMap).find(
                              key => featureMap[key].text === feature
                            )
                            const featureInfo = featureKey ? featureMap[featureKey] : { color: 'default', text: feature }
                            return (
                              <Tag key={index} color={featureInfo.color}>
                                {featureInfo.text}
                              </Tag>
                            )
                          })}
                        </Space>
                      ) : (
                        <Tag color="green">未检测到需要清洗的特征</Tag>
                      )}
                    </div>
                  </div>

                  {/* 详细信息 */}
                  <Descriptions bordered column={2}>
                    <Descriptions.Item label="文件名">
                      {analysisResult.filename}
                    </Descriptions.Item>
                    <Descriptions.Item label="人脸数量">
                      {analysisResult.analysis_result?.face_count || 0}
                    </Descriptions.Item>
                    <Descriptions.Item label="人脸状态">
                      {analysisResult.summary?.face_status || '未知'}
                    </Descriptions.Item>
                    <Descriptions.Item label="人物数量">
                      {analysisResult.analysis_result?.person_count || 0}
                    </Descriptions.Item>
                    <Descriptions.Item label="人物状态">
                      {analysisResult.summary?.person_status || '未知'}
                    </Descriptions.Item>
                    <Descriptions.Item label="文字状态">
                      {analysisResult.summary?.text_status || '未知'}
                    </Descriptions.Item>
                    <Descriptions.Item label="模糊状态" span={2}>
                      {analysisResult.summary?.blur_status || '未知'}
                    </Descriptions.Item>
                    {analysisResult.analysis_result?.face_locations && 
                     analysisResult.analysis_result.face_locations.length > 0 && (
                      <Descriptions.Item label="人脸位置" span={2}>
                        {analysisResult.analysis_result.face_locations.map((loc, idx) => (
                          <Tag key={idx} style={{ marginRight: 8 }}>
                            {idx + 1}: ({loc[0]}, {loc[1]}, {loc[2]}x{loc[3]})
                          </Tag>
                        ))}
                      </Descriptions.Item>
                    )}
                    {analysisResult.analysis_result?.person_locations && 
                     analysisResult.analysis_result.person_locations.length > 0 && (
                      <Descriptions.Item label="人物位置" span={2}>
                        {analysisResult.analysis_result.person_locations.map((loc, idx) => (
                          <Tag key={idx} style={{ marginRight: 8 }}>
                            {idx + 1}: ({loc[0]}, {loc[1]}, {loc[2]}x{loc[3]})
                          </Tag>
                        ))}
                      </Descriptions.Item>
                    )}
                    {analysisResult.analysis_result?.text_locations && 
                     analysisResult.analysis_result.text_locations.length > 0 && (
                      <Descriptions.Item label="文字位置" span={2}>
                        <Text type="secondary">检测到 {analysisResult.analysis_result.text_locations.length} 个文字区域（已在标注图中用蓝色方框标注）</Text>
                      </Descriptions.Item>
                    )}
                  </Descriptions>

                  {/* 标注结果图 */}
                  {analysisResult && imageUrl && (
                    <Card size="small" title="标注结果图" style={{ marginTop: 16 }}>
                      <AnnotatedImage
                        imageUrl={imageUrl}
                        faceLocations={analysisResult.analysis_result?.face_locations || []}
                        textLocations={analysisResult.analysis_result?.text_locations || []}
                      />
                      <div style={{ marginTop: 8, fontSize: '12px', color: '#999' }}>
                        <Tag color="red">红色方框：人脸</Tag>
                        <Tag color="blue" style={{ marginLeft: 8 }}>蓝色方框：文字</Tag>
                      </div>
                    </Card>
                  )}

                  {/* 原始数据 */}
                  <Card size="small" title="原始数据" style={{ marginTop: 16 }}>
                    <pre style={{ 
                      background: '#f5f5f5', 
                      padding: '12px', 
                      borderRadius: '4px',
                      overflow: 'auto',
                      maxHeight: '300px'
                    }}>
                      {JSON.stringify(analysisResult.analysis_result, null, 2)}
                    </pre>
                  </Card>
                </Space>
              </Card>
            )}
          </Space>
        </div>
      </Card>
    </div>
  )
}

export default ImageCleaningTest

