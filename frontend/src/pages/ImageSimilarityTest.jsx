import React, { useState } from 'react'
import {
  Card,
  Upload,
  Button,
  Space,
  message,
  Typography,
  Row,
  Col,
  Image,
  Progress,
  Divider,
  Select
} from 'antd'
import { UploadOutlined, ReloadOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Title, Text } = Typography

const ImageSimilarityTest = () => {
  const [image1, setImage1] = useState(null)
  const [image2, setImage2] = useState(null)
  const [image1Preview, setImage1Preview] = useState(null)
  const [image2Preview, setImage2Preview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [method, setMethod] = useState('histogram') // 默认使用灰度直方图方法

  const handleImage1Change = (info) => {
    const file = info.file.originFileObj || info.file
    if (file && file instanceof File) {
      setImage1(file)
      const reader = new FileReader()
      reader.onload = (e) => {
        setImage1Preview(e.target.result)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleImage2Change = (info) => {
    const file = info.file.originFileObj || info.file
    if (file && file instanceof File) {
      setImage2(file)
      const reader = new FileReader()
      reader.onload = (e) => {
        setImage2Preview(e.target.result)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleCalculate = async () => {
    if (!image1 || !image2) {
      message.error('请上传两张图片')
      return
    }

    setLoading(true)
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('image1', image1)
      formData.append('image2', image2)
      formData.append('method', method)

      const response = await api.post('/tools/image-similarity', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      if (response.code === 200) {
        setResult(response.data)
        message.success('相似度计算完成')
      } else {
        message.error(response.message || '计算失败')
      }
    } catch (error) {
      message.error('计算失败：' + (error.response?.data?.message || error.message))
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setImage1(null)
    setImage2(null)
    setImage1Preview(null)
    setImage2Preview(null)
    setResult(null)
    setMethod('histogram')
  }

  const getSimilarityColor = (similarity, method) => {
    if (method === 'psnr') {
      // PSNR: >40dB很好，30-40dB较好，20-30dB一般，<20dB较差
      if (similarity >= 40) return '#52c41a'
      if (similarity >= 30) return '#1890ff'
      if (similarity >= 20) return '#faad14'
      return '#ff4d4f'
    } else if (method === 'euclidean') {
      // 欧氏距离：显示的是距离值，越小越好，但这里similarity已经是转换后的相似度（0-1）
      // 所以使用相同的颜色判断逻辑
      if (similarity >= 0.8) return '#52c41a' // 绿色 - 非常相似
      if (similarity >= 0.6) return '#1890ff' // 蓝色 - 较相似
      if (similarity >= 0.4) return '#faad14' // 橙色 - 一般相似
      return '#ff4d4f' // 红色 - 不相似
    } else {
      // histogram和ssim: 0-1范围
      if (similarity >= 0.8) return '#52c41a' // 绿色 - 非常相似
      if (similarity >= 0.6) return '#1890ff' // 蓝色 - 较相似
      if (similarity >= 0.4) return '#faad14' // 橙色 - 一般相似
      return '#ff4d4f' // 红色 - 不相似
    }
  }

  const getSimilarityText = (similarity, method) => {
    if (method === 'psnr') {
      if (similarity === Infinity || similarity >= 40) return '图像完全相同/质量极好'
      if (similarity >= 30) return '质量较好'
      if (similarity >= 20) return '质量一般'
      return '质量较差'
    } else if (method === 'euclidean') {
      // 欧氏距离：similarity已经是转换后的相似度（0-1）
      if (similarity >= 0.8) return '非常相似'
      if (similarity >= 0.6) return '较相似'
      if (similarity >= 0.4) return '一般相似'
      if (similarity >= 0.2) return '不太相似'
      return '很不相似'
    } else {
      if (similarity >= 0.8) return '非常相似'
      if (similarity >= 0.6) return '较相似'
      if (similarity >= 0.4) return '一般相似'
      if (similarity >= 0.2) return '不太相似'
      return '很不相似'
    }
  }

  const getMethodDescription = (method) => {
    const descriptions = {
      histogram: '基于灰度直方图特征计算，使用余弦相似度算法。算法先将图片转为灰度图并统一尺寸为256×256，然后提取256维灰度直方图特征，最后计算特征向量的余弦相似度。相似度值范围0-1，越接近1表示两张图片越相似。',
      psnr: 'PSNR（峰值信噪比）是一种基于像素误差的图像质量评估指标。PSNR值以dB为单位，值越大表示图像质量越好。通常PSNR>30dB表示质量较好，>40dB表示质量很好。如果两张图片完全相同，PSNR为无穷大。',
      ssim: 'SSIM（结构相似性指数）是一种基于感知的图像质量评估指标，考虑了亮度、对比度和结构三个方面的相似性。SSIM值范围0-1，越接近1表示两张图片越相似。SSIM比PSNR更符合人眼视觉感知。',
      euclidean: '基于图像像素的欧氏距离计算相似度。算法将两张图片调整为相同尺寸，然后计算所有像素值的欧氏距离（差值平方和的平方根）。距离越小，相似度越高。相似度值范围0-1，越接近1表示两张图片越相似。'
    }
    return descriptions[method] || descriptions.histogram
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Title level={3}>图片相似度测试</Title>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Text type="secondary">
              上传两张图片，系统将计算它们之间的相似度
            </Text>
            <Space>
              <Text>计算方法：</Text>
              <Select
                value={method}
                onChange={setMethod}
                disabled={loading}
                style={{ width: 200 }}
                options={[
                  { label: '灰度直方图（余弦相似度）', value: 'histogram' },
                  { label: 'PSNR（峰值信噪比）', value: 'psnr' },
                  { label: 'SSIM（结构相似性）', value: 'ssim' },
                  { label: '像素欧氏距离', value: 'euclidean' }
                ]}
              />
            </Space>
          </Space>

          <Row gutter={24}>
            <Col xs={24} sm={12}>
              <Card title="图片1" size="small">
                <Upload
                  accept="image/*"
                  showUploadList={false}
                  beforeUpload={() => false}
                  onChange={handleImage1Change}
                >
                  <Button icon={<UploadOutlined />}>选择图片1</Button>
                </Upload>
                {image1Preview && (
                  <div style={{ marginTop: 16 }}>
                    <Image
                      src={image1Preview}
                      alt="图片1预览"
                      style={{ maxWidth: '100%', maxHeight: '300px' }}
                      preview={true}
                    />
                    {image1 && (
                      <div style={{ marginTop: 8 }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          文件名: {image1.name}
                        </Text>
                      </div>
                    )}
                  </div>
                )}
              </Card>
            </Col>

            <Col xs={24} sm={12}>
              <Card title="图片2" size="small">
                <Upload
                  accept="image/*"
                  showUploadList={false}
                  beforeUpload={() => false}
                  onChange={handleImage2Change}
                >
                  <Button icon={<UploadOutlined />}>选择图片2</Button>
                </Upload>
                {image2Preview && (
                  <div style={{ marginTop: 16 }}>
                    <Image
                      src={image2Preview}
                      alt="图片2预览"
                      style={{ maxWidth: '100%', maxHeight: '300px' }}
                      preview={true}
                    />
                    {image2 && (
                      <div style={{ marginTop: 8 }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          文件名: {image2.name}
                        </Text>
                      </div>
                    )}
                  </div>
                )}
              </Card>
            </Col>
          </Row>

          <Space>
            <Button
              type="primary"
              onClick={handleCalculate}
              loading={loading}
              disabled={!image1 || !image2}
            >
              计算相似度
            </Button>
            <Button icon={<ReloadOutlined />} onClick={handleReset}>
              重置
            </Button>
          </Space>

          {result && (
            <Card title="相似度结果" style={{ marginTop: 24 }}>
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                <div style={{ textAlign: 'center' }}>
                  <div style={{ marginBottom: 8 }}>
                    <Text type="secondary" style={{ fontSize: 14 }}>
                      使用方法：{result.method_name}
                    </Text>
                  </div>
                  <div style={{ marginBottom: 16 }}>
                    <Text strong style={{ fontSize: 16 }}>
                      {result.method === 'psnr' ? 'PSNR值：' : result.method === 'euclidean' ? '欧氏距离：' : '相似度评分：'}
                    </Text>
                    <Text
                      strong
                      style={{
                        fontSize: 48,
                        color: getSimilarityColor(result.result_value, result.method),
                        marginLeft: 16
                      }}
                    >
                      {result.method === 'psnr' 
                        ? (result.result_value === Infinity ? '∞' : `${result.result_percent} dB`)
                        : result.method === 'euclidean'
                        ? `${result.result_value.toFixed(2)}`
                        : `${result.similarity_percent}%`
                      }
                    </Text>
                  </div>
                  {result.method !== 'psnr' && result.method !== 'euclidean' && (
                    <Progress
                      type="circle"
                      percent={result.similarity_percent}
                      strokeColor={getSimilarityColor(result.similarity, result.method)}
                      format={(percent) => `${percent}%`}
                      style={{ marginBottom: 16 }}
                    />
                  )}
                  {result.method === 'euclidean' && (
                    <div style={{ marginBottom: 16 }}>
                      <Text type="secondary" style={{ fontSize: 14 }}>
                        相似度评分：{result.similarity_percent}%
                      </Text>
                    </div>
                  )}
                  <div>
                    <Text
                      style={{
                        fontSize: 18,
                        color: getSimilarityColor(result.result_value, result.method)
                      }}
                    >
                      {getSimilarityText(result.result_value, result.method)}
                    </Text>
                  </div>
                </div>

                <Divider />

                <Row gutter={16}>
                  <Col span={12}>
                    <Card size="small" title="图片1信息">
                      <Space direction="vertical">
                        <Text>文件名: {result.image1.filename}</Text>
                        <Text>尺寸: {result.image1.size[0]} × {result.image1.size[1]}</Text>
                        <Text>模式: {result.image1.mode}</Text>
                      </Space>
                    </Card>
                  </Col>
                  <Col span={12}>
                    <Card size="small" title="图片2信息">
                      <Space direction="vertical">
                        <Text>文件名: {result.image2.filename}</Text>
                        <Text>尺寸: {result.image2.size[0]} × {result.image2.size[1]}</Text>
                        <Text>模式: {result.image2.mode}</Text>
                      </Space>
                    </Card>
                  </Col>
                </Row>

                <div style={{ marginTop: 16 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    说明：{getMethodDescription(result.method)}
                  </Text>
                </div>
              </Space>
            </Card>
          )}
        </Space>
      </Card>
    </div>
  )
}

export default ImageSimilarityTest
