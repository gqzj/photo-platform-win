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
  Select,
  Form,
  Input,
  Popconfirm
} from 'antd'
import { ClusterOutlined, EyeOutlined, ReloadOutlined, DeleteOutlined, SaveOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Title, Text } = Typography
const { TextArea } = Input

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
  const [clusterMetric, setClusterMetric] = useState('lightweight_7d') // 聚类指标：默认使用轻量7维特征
  const [clusterAlgorithm, setClusterAlgorithm] = useState('kmeans') // 聚类算法：默认使用K-Means
  const [reuseImages, setReuseImages] = useState(true) // 默认复用已生成的图片
  const [previewModalVisible, setPreviewModalVisible] = useState(false)
  const [previewFile, setPreviewFile] = useState(null)
  const [saveSnapshotModalVisible, setSaveSnapshotModalVisible] = useState(false)
  const [snapshotForm] = Form.useForm()
  const [reclusterModalVisible, setReclusterModalVisible] = useState(false)
  const [reclusterForm] = Form.useForm()
  const [reclusteringClusterId, setReclusteringClusterId] = useState(null)
  const [reclustering, setReclustering] = useState(false)

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
        metric: clusterMetric,
        algorithm: clusterAlgorithm,
        reuse_images: reuseImages
      })

      if (response.code === 200) {
        const metricName = response.data?.metric_name || '未知指标'
        const algorithmName = response.data?.algorithm_name || '未知算法'
        message.success(`聚类分析完成（使用${metricName}指标和${algorithmName}算法）`)
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
      // clusterId可能是字符串（如"0-1"）或数字
      const clusterIdStr = typeof clusterId === 'string' ? clusterId : clusterId.toString()
      const response = await api.get(`/lut-files/cluster/${clusterIdStr}/files`, {
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

  const handleDistill = async (clusterId, lutFileId) => {
    try {
      const response = await api.post(`/lut-files/cluster/${clusterId}/distill/${lutFileId}`)
      if (response.code === 200) {
        message.success('蒸馏成功')
        // 刷新文件列表和统计
        await fetchClusterFiles(selectedClusterId, filesPagination.current)
        await fetchClusterStats()
        // 如果当前聚类没有文件了，清空选择
        if (clusterFiles.length === 1) {
          setSelectedClusterId(null)
          setClusterFiles([])
        }
      } else {
        message.error(response.message || '蒸馏失败')
      }
    } catch (error) {
      message.error('蒸馏失败：' + (error.response?.data?.message || error.message))
    }
  }

  const handleRecluster = async () => {
    try {
      const values = await reclusterForm.validateFields()
      if (!reclusteringClusterId && reclusteringClusterId !== 0 && reclusteringClusterId !== '0') {
        message.error('请选择要再次聚类的聚类')
        return
      }

      setReclustering(true)
      try {
        // 支持子聚类再次聚类，clusterId可能是字符串（如"1-2"）
        const clusterIdStr = typeof reclusteringClusterId === 'string' ? reclusteringClusterId : reclusteringClusterId.toString()
        const response = await api.post(`/lut-files/cluster/${clusterIdStr}/recluster`, {
          n_clusters: values.n_clusters,
          reuse_images: values.reuse_images !== false
        })

        if (response.code === 200) {
          const metricName = response.data?.metric_name || '未知指标'
          const algorithmName = response.data?.algorithm_name || '未知算法'
          message.success(`再次聚类完成（使用${metricName}指标和${algorithmName}算法）`)
          await fetchClusterStats()
          setReclusterModalVisible(false)
          setReclusteringClusterId(null)
          reclusterForm.resetFields()
          setSelectedClusterId(null)
          setClusterFiles([])
        } else {
          message.error(response.message || '再次聚类失败')
        }
      } catch (error) {
        message.error('再次聚类失败：' + (error.response?.data?.message || error.message))
      } finally {
        setReclustering(false)
      }
    } catch (error) {
      if (error.errorFields) {
        // 表单验证错误
        return
      }
      message.error('再次聚类失败：' + (error.response?.data?.message || error.message))
    }
  }

  const handleDeleteCluster = async (clusterId) => {
    try {
      const response = await api.delete(`/lut-files/cluster/${clusterId}`)
      if (response.code === 200) {
        message.success(`聚类 ${clusterId} 删除成功`)
        // 刷新统计
        await fetchClusterStats()
        // 如果删除的是当前选中的聚类，清空选择
        if (selectedClusterId === clusterId || selectedClusterId === clusterId.toString()) {
          setSelectedClusterId(null)
          setClusterFiles([])
        }
      } else {
        message.error(response.message || '删除失败')
      }
    } catch (error) {
      message.error('删除失败：' + (error.response?.data?.message || error.message))
    }
  }

  const handleSaveSnapshot = async () => {
    try {
      const values = await snapshotForm.validateFields()
      const response = await api.post('/lut-files/cluster/snapshot', {
        name: values.name,
        description: values.description || '',
        metric: clusterMetric,
        metric_name: clusterMetric === 'lightweight_7d' ? '轻量7维特征' :
                     clusterMetric === 'image_features' ? '图像特征映射' :
                     clusterMetric === 'image_similarity' ? '图片相似度' :
                     clusterMetric === 'ssim' ? 'SSIM（结构相似性）' :
                     clusterMetric === 'euclidean' ? '像素欧氏距离' : '未知',
        algorithm: clusterAlgorithm,
        algorithm_name: clusterAlgorithm === 'kmeans' ? 'K-Means' : '凝聚式层次聚类'
      })
      if (response.code === 200) {
        message.success('快照保存成功')
        setSaveSnapshotModalVisible(false)
        snapshotForm.resetFields()
      } else {
        message.error(response.message || '保存快照失败')
      }
    } catch (error) {
      if (error.errorFields) {
        // 表单验证错误
        return
      }
      message.error('保存快照失败：' + (error.response?.data?.message || error.message))
    }
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
              <Text>聚类指标：</Text>
              <Select
                value={clusterMetric}
                onChange={(value) => {
                  setClusterMetric(value)
                  // 如果选择image_similarity、ssim或euclidean，自动切换到层次聚类
                  if (value === 'image_similarity' || value === 'ssim' || value === 'euclidean') {
                    setClusterAlgorithm('hierarchical')
                  }
                }}
                disabled={clustering}
                style={{ width: 180 }}
                options={[
                  { label: '轻量7维特征', value: 'lightweight_7d' },
                  { label: '图像特征映射', value: 'image_features' },
                  { label: '图片相似度', value: 'image_similarity' },
                  { label: 'SSIM（结构相似性）', value: 'ssim' },
                  { label: '像素欧氏距离', value: 'euclidean' }
                ]}
              />
              <Text>聚类算法：</Text>
              <Select
                value={clusterAlgorithm}
                onChange={setClusterAlgorithm}
                disabled={clustering || clusterMetric === 'image_similarity' || clusterMetric === 'ssim' || clusterMetric === 'euclidean'}
                style={{ width: 150 }}
                options={[
                  { label: 'K-Means', value: 'kmeans' },
                  { label: '凝聚式层次聚类', value: 'hierarchical' }
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
              {(clusterMetric === 'image_similarity' || clusterMetric === 'ssim' || clusterMetric === 'euclidean') && (
                <>
                  <Text>复用图片：</Text>
                  <Select
                    value={reuseImages}
                    onChange={setReuseImages}
                    disabled={clustering}
                    style={{ width: 100 }}
                    options={[
                      { label: '是', value: true },
                      { label: '否', value: false }
                    ]}
                  />
                </>
              )}
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
              {clusterStats && clusterStats.total_clusters > 0 && (
                <Button
                  type="default"
                  icon={<SaveOutlined />}
                  onClick={() => setSaveSnapshotModalVisible(true)}
                >
                  保存快照
                </Button>
              )}
            </Space>
          </div>

          <Spin spinning={loading}>
            {clusterStats && clusterStats.total_clusters > 0 ? (
              <>
                <Card title="聚类统计" size="small">
                  <Row gutter={[16, 16]}>
                    <Col span={24}>
                      <Space direction="vertical" size="small" style={{ width: '100%' }}>
                        <div>
                          <Text strong>总聚类数：</Text>
                          <Text>{clusterStats.total_clusters}</Text>
                          <Text strong style={{ marginLeft: 16 }}>总文件数：</Text>
                          <Text>{clusterStats.total_files}</Text>
                        </div>
                        <div>
                          {clusterStats.metric_name ? (
                            <>
                              <Text strong>聚类指标：</Text>
                              <Tag color="blue">{clusterStats.metric_name}</Tag>
                            </>
                          ) : (
                            <>
                              <Text strong>聚类指标：</Text>
                              <Text type="secondary">未知（请保存快照以查看详细信息）</Text>
                            </>
                          )}
                          {clusterStats.algorithm_name ? (
                            <>
                              <Text strong style={{ marginLeft: 16 }}>聚类算法：</Text>
                              <Tag color="green">{clusterStats.algorithm_name}</Tag>
                            </>
                          ) : (
                            <>
                              <Text strong style={{ marginLeft: 16 }}>聚类算法：</Text>
                              <Text type="secondary">未知（请保存快照以查看详细信息）</Text>
                            </>
                          )}
                        </div>
                      </Space>
                    </Col>
                    {Object.entries(clusterStats.cluster_stats || {}).map(([clusterId, count]) => {
                      // 解析clusterId，判断是否为子聚类
                      const isSubCluster = clusterId.includes('-')
                      const clusterIdNum = isSubCluster ? parseInt(clusterId.split('-')[0]) : parseInt(clusterId)
                      const isTopLevel = !isSubCluster
                      
                      return (
                        <Col xs={12} sm={8} md={6} lg={4} key={clusterId}>
                          <Card
                            hoverable
                            style={{
                              textAlign: 'center',
                              cursor: 'pointer',
                              borderColor: selectedClusterId === clusterId || selectedClusterId === clusterId.toString() ? '#1890ff' : undefined
                            }}
                            onClick={() => setSelectedClusterId(clusterId)}
                            actions={[
                              <Button
                                key="recluster"
                                type="link"
                                size="small"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  // 支持子聚类再次聚类，直接使用clusterId字符串
                                  setReclusteringClusterId(clusterId)
                                  reclusterForm.setFieldsValue({ n_clusters: 3, reuse_images: true })
                                  setReclusterModalVisible(true)
                                }}
                                disabled={reclustering}
                              >
                                再次聚类
                              </Button>,
                              <Popconfirm
                                key="delete"
                                title={`确定要删除聚类 ${clusterId} 吗？`}
                                description="删除后该聚类中的文件将不再显示"
                                onConfirm={(e) => {
                                  e?.stopPropagation()
                                  handleDeleteCluster(clusterId)
                                }}
                                onCancel={(e) => {
                                  e?.stopPropagation()
                                }}
                                okText="确定"
                                cancelText="取消"
                              >
                                <Button
                                  type="link"
                                  danger
                                  size="small"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                  }}
                                >
                                  删除
                                </Button>
                              </Popconfirm>
                            ]}
                          >
                            <Tag color={getClusterColor(clusterIdNum)} style={{ fontSize: 16, padding: '4px 12px' }}>
                              聚类 {clusterId}
                            </Tag>
                            <div style={{ marginTop: 8, fontSize: 18, fontWeight: 'bold' }}>
                              {count} 个文件
                            </div>
                          </Card>
                        </Col>
                      )
                    })}
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
                                      <Text type="secondary" style={{ fontSize: '11px' }}>
                                        ID: {file.id}
                                      </Text>
                                    </div>
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
                                  <Space style={{ marginTop: '8px', width: '100%' }} direction="vertical" size="small">
                                    <Button
                                      type="primary"
                                      size="small"
                                      icon={<EyeOutlined />}
                                      onClick={() => handlePreview(file)}
                                      block
                                    >
                                      预览
                                    </Button>
                                    <Popconfirm
                                      title="确定要蒸馏这个LUT文件吗？"
                                      description="蒸馏后该文件将不再显示在当前聚类中"
                                      onConfirm={() => handleDistill(selectedClusterId, file.id)}
                                      okText="确定"
                                      cancelText="取消"
                                    >
                                      <Button
                                        danger
                                        size="small"
                                        icon={<DeleteOutlined />}
                                        block
                                      >
                                        蒸馏
                                      </Button>
                                    </Popconfirm>
                                  </Space>
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
            {/* 缩略图 */}
            {previewFile.thumbnail_path ? (
              <div style={{ 
                marginBottom: '24px', 
                textAlign: 'center',
                backgroundColor: '#f5f5f5',
                padding: '20px',
                borderRadius: '8px'
              }}>
                <Image
                  src={`/api/lut-files/${previewFile.id}/thumbnail`}
                  alt={previewFile.original_filename}
                  style={{ 
                    maxWidth: '100%',
                    maxHeight: '400px',
                    objectFit: 'contain'
                  }}
                  preview={true}
                />
              </div>
            ) : (
              <div style={{ 
                marginBottom: '24px', 
                textAlign: 'center',
                backgroundColor: '#f5f5f5',
                padding: '40px',
                borderRadius: '8px',
                color: '#999'
              }}>
                无缩略图
              </div>
            )}
            
            <div style={{ marginBottom: '12px' }}>
              <Text strong>文件名：</Text>
              <Text>{previewFile.original_filename}</Text>
            </div>
            <div style={{ marginBottom: '12px' }}>
              <Text strong>类别：</Text>
              <Text>{previewFile.category_name || '未分类'}</Text>
            </div>
            {previewFile.tag && (
              <div style={{ marginBottom: '12px' }}>
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

      {/* 保存快照模态框 */}
      <Modal
        title="保存聚类快照"
        open={saveSnapshotModalVisible}
        onOk={handleSaveSnapshot}
        onCancel={() => {
          setSaveSnapshotModalVisible(false)
          snapshotForm.resetFields()
        }}
        okText="保存"
        cancelText="取消"
      >
        <Form form={snapshotForm} layout="vertical">
          <Form.Item
            name="name"
            label="快照名称"
            rules={[{ required: true, message: '请输入快照名称' }]}
          >
            <Input placeholder="请输入快照名称" />
          </Form.Item>
          <Form.Item
            name="description"
            label="快照描述"
          >
            <TextArea rows={4} placeholder="请输入快照描述（可选）" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 再次聚类模态框 */}
      <Modal
        title={`对聚类 ${typeof reclusteringClusterId === 'string' ? reclusteringClusterId : reclusteringClusterId} 进行再次聚类`}
        open={reclusterModalVisible}
        onOk={handleRecluster}
        onCancel={() => {
          setReclusterModalVisible(false)
          setReclusteringClusterId(null)
          reclusterForm.resetFields()
        }}
        okText="开始聚类"
        cancelText="取消"
        confirmLoading={reclustering}
      >
        <Form form={reclusterForm} layout="vertical">
          <Form.Item
            name="n_clusters"
            label="子聚类数"
            rules={[{ required: true, message: '请输入子聚类数' }]}
            initialValue={3}
          >
            <InputNumber
              min={2}
              max={20}
              style={{ width: '100%' }}
              placeholder="请输入子聚类数（2-20）"
            />
          </Form.Item>
          <Form.Item
            name="reuse_images"
            label="复用图片"
            initialValue={true}
          >
            <Select
              options={[
                { label: '是', value: true },
                { label: '否', value: false }
              ]}
            />
          </Form.Item>
          <Text type="secondary" style={{ fontSize: 12 }}>
            再次聚类将使用与父聚类相同的指标和算法，子聚类编号格式为：父编号-自编号（如：{typeof reclusteringClusterId === 'string' ? reclusteringClusterId : reclusteringClusterId}-0, {typeof reclusteringClusterId === 'string' ? reclusteringClusterId : reclusteringClusterId}-1）
          </Text>
        </Form>
      </Modal>
    </div>
  )
}

export default LutClusterAnalysis

