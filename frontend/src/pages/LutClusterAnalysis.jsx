import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Card,
  Button,
  Space,
  message,
  InputNumber,
  Spin,
  Row,
  Col,
  Tag,
  Typography,
  Empty,
  Modal,
  Image,
  Pagination,
  Select
} from 'antd'
import { ClusterOutlined, EyeOutlined, ReloadOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Title, Text } = Typography

const LutClusterAnalysis = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [clustering, setClustering] = useState(false)
  const [clusterStats, setClusterStats] = useState(null)
  const [selectedClusterId, setSelectedClusterId] = useState(null)
  const [clusterFiles, setClusterFiles] = useState([])
  const [filesLoading, setFilesLoading] = useState(false)
  const [filesPagination, setFilesPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  })
  const [nClusters, setNClusters] = useState(5)
  const [clusterMethod, setClusterMethod] = useState('lightweight_7d') // 默认使用轻量7维特征
  const [previewModalVisible, setPreviewModalVisible] = useState(false)
  const [previewFile, setPreviewFile] = useState(null)

  useEffect(() => {
    fetchClusterStats()
  }, [])

  useEffect(() => {
    if (selectedClusterId !== null) {
      fetchClusterFiles(selectedClusterId, 1)
    }
  }, [selectedClusterId])

  const fetchClusterStats = async () => {
    setLoading(true)
    try {
      const response = await api.get('/lut-files/cluster/stats')
      if (response.code === 200) {
        setClusterStats(response.data)
      } else {
        message.error(response.message || '获取聚类统计失败')
      }
    } catch (error) {
      message.error('获取聚类统计失败：' + (error.response?.data?.message || error.message))
    } finally {
      setLoading(false)
    }
  }

  const handleCluster = async () => {
    if (nClusters < 2) {
      message.error('聚类数必须大于等于2')
      return
    }

    setClustering(true)
    try {
      const response = await api.post('/lut-files/cluster', {
        n_clusters: nClusters,
        method: clusterMethod
      })

      if (response.code === 200) {
        const methodNameMap = {
          'lightweight_7d': '轻量7维特征',
          'image_features': '图像特征映射',
          'image_similarity': '图片相似度',
          'ssim': 'SSIM（结构相似性）'
        }
        const methodName = response.data?.method_name || methodNameMap[clusterMethod] || '未知方法'
        message.success(`聚类分析完成（使用${methodName}方法）`)
        await fetchClusterStats()
        setSelectedClusterId(null)
        setClusterFiles([])
      } else {
        message.error(response.message || '聚类分析失败')
      }
    } catch (error) {
      message.error('聚类分析失败：' + (error.response?.data?.message || error.message))
    } finally {
      setClustering(false)
    }
  }

  const fetchClusterFiles = async (clusterId, page = 1) => {
    setFilesLoading(true)
    try {
      const response = await api.get(`/lut-files/cluster/${clusterId}/files`, {
        params: {
          page: page,
          page_size: filesPagination.pageSize
        }
      })

      if (response.code === 200) {
        setClusterFiles(response.data.list || [])
        setFilesPagination({
          ...filesPagination,
          current: response.data.page,
          total: response.data.total
        })
      } else {
        message.error(response.message || '获取文件列表失败')
      }
    } catch (error) {
      message.error('获取文件列表失败：' + (error.response?.data?.message || error.message))
    } finally {
      setFilesLoading(false)
    }
  }

  const handlePageChange = (page) => {
    fetchClusterFiles(selectedClusterId, page)
  }

  const handlePreview = (file) => {
    setPreviewFile(file)
    setPreviewModalVisible(true)
  }

  const getClusterColor = (clusterId) => {
    const colors = ['red', 'blue', 'green', 'orange', 'purple', 'cyan', 'magenta', 'gold', 'lime', 'volcano']
    return colors[clusterId % colors.length]
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Title level={3} style={{ margin: 0 }}>LUT聚类分析</Title>
            <Space>
              <Text>聚类方法：</Text>
              <Select
                value={clusterMethod}
                onChange={setClusterMethod}
                disabled={clustering}
                style={{ width: 180 }}
                options={[
                  { label: '轻量7维特征', value: 'lightweight_7d' },
                  { label: '图像特征映射', value: 'image_features' },
                  { label: '图片相似度', value: 'image_similarity' },
                  { label: 'SSIM（结构相似性）', value: 'ssim' }
                ]}
              />
              <Text>聚类数：</Text>
              <InputNumber
                min={2}
                max={100}
                value={nClusters}
                onChange={(value) => setNClusters(value || 5)}
                disabled={clustering}
              />
              <Button
                type="primary"
                icon={<ClusterOutlined />}
                onClick={handleCluster}
                loading={clustering}
              >
                执行聚类
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={fetchClusterStats}
                loading={loading}
              >
                刷新
              </Button>
            </Space>
          </div>

          <Spin spinning={loading}>
            {clusterStats && clusterStats.total_clusters > 0 ? (
              <>
                <Card title="聚类统计" size="small">
                  <Row gutter={[16, 16]}>
                    <Col span={24}>
                      <Text strong>总聚类数：{clusterStats.total_clusters}</Text>
                      <Text style={{ marginLeft: 16 }}>总文件数：{clusterStats.total_files}</Text>
                    </Col>
                    {Object.entries(clusterStats.cluster_stats || {}).map(([clusterId, count]) => (
                      <Col xs={12} sm={8} md={6} lg={4} key={clusterId}>
                        <Card
                          hoverable
                          style={{
                            textAlign: 'center',
                            cursor: 'pointer',
                            borderColor: selectedClusterId === parseInt(clusterId) ? '#1890ff' : undefined
                          }}
                          onClick={() => setSelectedClusterId(parseInt(clusterId))}
                        >
                          <Tag color={getClusterColor(parseInt(clusterId))} style={{ fontSize: 16, padding: '4px 12px' }}>
                            聚类 {clusterId}
                          </Tag>
                          <div style={{ marginTop: 8, fontSize: 18, fontWeight: 'bold' }}>
                            {count} 个文件
                          </div>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </Card>

                {selectedClusterId !== null && (
                  <Card title={`聚类 ${selectedClusterId} 的文件列表`}>
                    <Spin spinning={filesLoading}>
                      {clusterFiles.length > 0 ? (
                        <>
                          <Row gutter={[16, 16]}>
                            {clusterFiles.map((file) => (
                              <Col xs={12} sm={8} md={6} lg={4} xl={4} key={file.id}>
                                <Card
                                  hoverable
                                  style={{
                                    height: '100%',
                                    display: 'flex',
                                    flexDirection: 'column'
                                  }}
                                  bodyStyle={{
                                    padding: '12px',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    flex: 1
                                  }}
                                  cover={
                                    file.thumbnail_path ? (
                                      <div style={{ 
                                        width: '100%', 
                                        height: '250px', 
                                        display: 'flex', 
                                        alignItems: 'center', 
                                        justifyContent: 'center',
                                        backgroundColor: '#f5f5f5',
                                        overflow: 'hidden'
                                      }}>
                                        <Image
                                          src={`/api/lut-files/${file.id}/thumbnail`}
                                          alt={file.original_filename}
                                          style={{ 
                                            width: '100%', 
                                            height: '100%', 
                                            objectFit: 'cover' 
                                          }}
                                          preview={false}
                                        />
                                      </div>
                                    ) : (
                                      <div style={{ 
                                        width: '100%', 
                                        height: '250px', 
                                        display: 'flex', 
                                        alignItems: 'center', 
                                        justifyContent: 'center',
                                        backgroundColor: '#f5f5f5',
                                        color: '#999'
                                      }}>
                                        无缩略图
                                      </div>
                                    )
                                  }
                                >
                                  <div style={{ flex: 1 }}>
                                    <Typography.Text
                                      strong
                                      ellipsis
                                      style={{
                                        display: 'block',
                                        marginBottom: '8px',
                                        fontSize: '13px'
                                      }}
                                      title={file.original_filename}
                                    >
                                      {file.original_filename}
                                    </Typography.Text>
                                    <div style={{ marginBottom: '8px' }}>
                                      <Text type="secondary" style={{ fontSize: '12px' }}>
                                        {file.category_name || '未分类'}
                                      </Text>
                                    </div>
                                    {file.tag && (
                                      <div style={{ marginBottom: '8px' }}>
                                        <Space size={[4, 4]} wrap>
                                          {file.tag.tone && (
                                            <Tag color="orange" style={{ fontSize: '11px', margin: 0 }}>
                                              {file.tag.tone}
                                            </Tag>
                                          )}
                                          {file.tag.saturation && (
                                            <Tag color="blue" style={{ fontSize: '11px', margin: 0 }}>
                                              {file.tag.saturation}
                                            </Tag>
                                          )}
                                          {file.tag.contrast && (
                                            <Tag color="purple" style={{ fontSize: '11px', margin: 0 }}>
                                              {file.tag.contrast}
                                            </Tag>
                                          )}
                                        </Space>
                                      </div>
                                    )}
                                  </div>
                                  <Button
                                    type="primary"
                                    size="small"
                                    icon={<EyeOutlined />}
                                    onClick={() => handlePreview(file)}
                                    block
                                    style={{ marginTop: '8px' }}
                                  >
                                    预览
                                  </Button>
                                </Card>
                              </Col>
                            ))}
                          </Row>
                          {filesPagination.total > filesPagination.pageSize && (
                            <div style={{ marginTop: '24px', textAlign: 'center' }}>
                              <Pagination
                                current={filesPagination.current}
                                pageSize={filesPagination.pageSize}
                                total={filesPagination.total}
                                onChange={handlePageChange}
                                showTotal={(total) => `共 ${total} 条`}
                                showSizeChanger={false}
                              />
                            </div>
                          )}
                        </>
                      ) : (
                        <Empty description="该聚类暂无文件" />
                      )}
                    </Spin>
                  </Card>
                )}
              </>
            ) : (
              <Empty description="暂无聚类结果，请先执行聚类分析" />
            )}
          </Spin>
        </Space>
      </Card>

      {/* 预览模态框 */}
      <Modal
        title="文件预览"
        open={previewModalVisible}
        onCancel={() => setPreviewModalVisible(false)}
        footer={null}
        width={800}
      >
        {previewFile && (
          <div>
            <p><Text strong>文件名：</Text>{previewFile.original_filename}</p>
            <p><Text strong>类别：</Text>{previewFile.category_name || '未分类'}</p>
            {previewFile.tag && (
              <div>
                <Text strong>标签：</Text>
                <Space style={{ marginLeft: 8 }}>
                  {previewFile.tag.tone && <Tag color="orange">色调: {previewFile.tag.tone}</Tag>}
                  {previewFile.tag.saturation && <Tag color="blue">饱和度: {previewFile.tag.saturation}</Tag>}
                  {previewFile.tag.contrast && <Tag color="purple">对比度: {previewFile.tag.contrast}</Tag>}
                </Space>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default LutClusterAnalysis

