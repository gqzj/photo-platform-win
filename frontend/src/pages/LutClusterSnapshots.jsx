import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  message,
  Tag,
  Typography,
  Modal,
  Row,
  Col,
  Image,
  Pagination,
  Empty,
  Spin,
  Popconfirm
} from 'antd'
import { EyeOutlined, ReloadOutlined, DeleteOutlined } from '@ant-design/icons'
import api from '../services/api'

const { Title, Text } = Typography

const LutClusterSnapshots = () => {
  const [loading, setLoading] = useState(false)
  const [snapshots, setSnapshots] = useState([])
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  })
  const [previewModalVisible, setPreviewModalVisible] = useState(false)
  const [previewSnapshot, setPreviewSnapshot] = useState(null)
  const [clusterFilesModalVisible, setClusterFilesModalVisible] = useState(false)
  const [selectedClusterId, setSelectedClusterId] = useState(null)
  const [clusterFiles, setClusterFiles] = useState([])
  const [clusterFilesLoading, setClusterFilesLoading] = useState(false)
  const [clusterFilesPagination, setClusterFilesPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  })

  useEffect(() => {
    fetchSnapshots()
  }, [pagination.current])

  const fetchSnapshots = async () => {
    setLoading(true)
    try {
      const response = await api.get('/lut-files/cluster/snapshots', {
        params: {
          page: pagination.current,
          page_size: pagination.pageSize
        }
      })
      if (response.code === 200) {
        setSnapshots(response.data.list || [])
        setPagination({
          ...pagination,
          total: response.data.total
        })
      } else {
        message.error(response.message || '获取快照列表失败')
      }
    } catch (error) {
      message.error('获取快照列表失败：' + (error.response?.data?.message || error.message))
    } finally {
      setLoading(false)
    }
  }

  const handlePreview = async (snapshot) => {
    try {
      const response = await api.get(`/lut-files/cluster/snapshot/${snapshot.id}`)
      if (response.code === 200) {
        setPreviewSnapshot(response.data)
        setPreviewModalVisible(true)
      } else {
        message.error(response.message || '获取快照详情失败')
      }
    } catch (error) {
      message.error('获取快照详情失败：' + (error.response?.data?.message || error.message))
    }
  }

  const handlePageChange = (page) => {
    setPagination({ ...pagination, current: page })
  }

  const handleDelete = async (snapshot) => {
    try {
      const response = await api.delete(`/lut-files/cluster/snapshot/${snapshot.id}`)
      if (response.code === 200) {
        message.success('删除成功')
        // 刷新列表
        await fetchSnapshots()
        // 如果删除的是当前预览的快照，关闭预览
        if (previewSnapshot && previewSnapshot.id === snapshot.id) {
          setPreviewModalVisible(false)
          setPreviewSnapshot(null)
        }
      } else {
        message.error(response.message || '删除失败')
      }
    } catch (error) {
      message.error('删除失败：' + (error.response?.data?.message || error.message))
    }
  }

  const handleClusterClick = async (clusterId) => {
    setSelectedClusterId(clusterId)
    setClusterFilesModalVisible(true)
    await fetchClusterFiles(clusterId, 1)
  }

  const fetchClusterFiles = async (clusterId, page = 1) => {
    setClusterFilesLoading(true)
    try {
      // clusterId可能是字符串（如"1-4"）或数字
      const clusterIdStr = typeof clusterId === 'string' ? clusterId : clusterId.toString()
      const response = await api.get(`/lut-files/cluster/${clusterIdStr}/files`, {
        params: {
          page: page,
          page_size: clusterFilesPagination.pageSize
        }
      })

      if (response.code === 200) {
        setClusterFiles(response.data.list || [])
        setClusterFilesPagination({
          ...clusterFilesPagination,
          current: response.data.page,
          total: response.data.total
        })
      } else {
        message.error(response.message || '获取文件列表失败')
      }
    } catch (error) {
      message.error('获取文件列表失败：' + (error.response?.data?.message || error.message))
    } finally {
      setClusterFilesLoading(false)
    }
  }

  const handleClusterFilesPageChange = (page) => {
    fetchClusterFiles(selectedClusterId, page)
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80
    },
    {
      title: '快照名称',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true
    },
    {
      title: '聚类指标',
      dataIndex: 'metric_name',
      key: 'metric_name',
      width: 150
    },
    {
      title: '聚类算法',
      dataIndex: 'algorithm_name',
      key: 'algorithm_name',
      width: 150
    },
    {
      title: '聚类数',
      dataIndex: 'n_clusters',
      key: 'n_clusters',
      width: 100
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
      width: 180,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handlePreview(record)}
          >
            查看
          </Button>
          <Popconfirm
            title="确定要删除这个快照吗？"
            description="删除后无法恢复"
            onConfirm={() => handleDelete(record)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
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
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Title level={3} style={{ margin: 0 }}>LUT聚类快照</Title>
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchSnapshots}
              loading={loading}
            >
              刷新
            </Button>
          </div>

          <Table
            columns={columns}
            dataSource={snapshots}
            rowKey="id"
            loading={loading}
            pagination={false}
          />

          {pagination.total > 0 && (
            <div style={{ textAlign: 'right', marginTop: 16 }}>
              <Pagination
                current={pagination.current}
                pageSize={pagination.pageSize}
                total={pagination.total}
                onChange={handlePageChange}
                showTotal={(total) => `共 ${total} 条`}
                showSizeChanger={false}
              />
            </div>
          )}
        </Space>
      </Card>

      {/* 快照详情模态框 */}
      <Modal
        title="快照详情"
        open={previewModalVisible}
        onCancel={() => {
          setPreviewModalVisible(false)
          setPreviewSnapshot(null)
        }}
        footer={null}
        width={1200}
      >
        {previewSnapshot && (
          <div>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <div>
                <Text strong>快照名称：</Text>
                <Text>{previewSnapshot.name}</Text>
              </div>
              {previewSnapshot.description && (
                <div>
                  <Text strong>快照描述：</Text>
                  <Text>{previewSnapshot.description}</Text>
                </div>
              )}
              <div>
                <Text strong>聚类指标：</Text>
                <Tag>{previewSnapshot.metric_name || '未知'}</Tag>
                <Text strong style={{ marginLeft: 16 }}>聚类算法：</Text>
                <Tag>{previewSnapshot.algorithm_name || '未知'}</Tag>
                <Text strong style={{ marginLeft: 16 }}>聚类数：</Text>
                <Tag>{previewSnapshot.n_clusters}</Tag>
              </div>
              <div>
                <Text strong>创建时间：</Text>
                <Text>{previewSnapshot.created_at}</Text>
              </div>

              {previewSnapshot.cluster_data && (
                <div>
                  <Title level={5}>聚类详情</Title>
                  <Row gutter={[16, 16]}>
                    {Object.entries(previewSnapshot.cluster_data).map(([clusterId, clusterInfo]) => (
                      <Col xs={24} sm={12} md={8} lg={6} key={clusterId}>
                        <Card
                          title={`聚类 ${clusterId}`}
                          size="small"
                          style={{ 
                            height: '100%',
                            cursor: 'pointer'
                          }}
                          hoverable
                          onClick={() => handleClusterClick(clusterId)}
                        >
                          <div style={{ marginBottom: 8 }}>
                            <Text strong>文件数：</Text>
                            <Text>{clusterInfo.file_count || 0}</Text>
                          </div>
                          <div style={{ marginTop: 8 }}>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              点击查看文件列表
                            </Text>
                          </div>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </div>
              )}
            </Space>
          </div>
        )}
      </Modal>

      {/* 聚类文件列表模态框 */}
      <Modal
        title={`聚类 ${selectedClusterId} 的文件列表`}
        open={clusterFilesModalVisible}
        onCancel={() => {
          setClusterFilesModalVisible(false)
          setSelectedClusterId(null)
          setClusterFiles([])
        }}
        footer={null}
        width={1200}
      >
        <Spin spinning={clusterFilesLoading}>
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
                            height: '200px', 
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
                            height: '200px', 
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
                        {file.category_name && (
                          <div style={{ marginBottom: '8px' }}>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              {file.category_name}
                            </Text>
                          </div>
                        )}
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
                    </Card>
                  </Col>
                ))}
              </Row>
              {clusterFilesPagination.total > clusterFilesPagination.pageSize && (
                <div style={{ marginTop: '24px', textAlign: 'center' }}>
                  <Pagination
                    current={clusterFilesPagination.current}
                    pageSize={clusterFilesPagination.pageSize}
                    total={clusterFilesPagination.total}
                    onChange={handleClusterFilesPageChange}
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
      </Modal>
    </div>
  )
}

export default LutClusterSnapshots
