import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './components/Layout/MainLayout'
import ImageTagging from './pages/ImageTagging'
import CrawlerCookie from './pages/CrawlerCookie'
import CrawlerTask from './pages/CrawlerTask'
import ImageLibrary from './pages/ImageLibrary'
import PostList from './pages/PostList'
import SettingsDirectory from './pages/SettingsDirectory'
import FeatureManagement from './pages/FeatureManagement'
import DataCleaningTask from './pages/DataCleaningTask'
import ImageRecycle from './pages/ImageRecycle'
import TaggingTask from './pages/TaggingTask'
import ImageCleaningTest from './pages/ImageCleaningTest'
import ImageTaggingTest from './pages/ImageTaggingTest'
import SampleSetManagement from './pages/SampleSetManagement'
import SampleSetView from './pages/SampleSetView'
import KeywordView from './pages/KeywordView'
import FeatureAnalysis from './pages/FeatureAnalysis'
import FeatureGroupManagement from './pages/FeatureGroupManagement'
import RequirementManagement from './pages/RequirementManagement'
import RequirementProgress from './pages/RequirementProgress'
import StyleManagement from './pages/StyleManagement'
import StyleImageView from './pages/StyleImageView'
import StyleMatch from './pages/StyleMatch'

function App() {
  return (
    <Router>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Navigate to="/library/images" replace />} />
          <Route path="/library/images" element={<ImageLibrary />} />
          <Route path="/library/posts" element={<PostList />} />
          <Route path="/library/keywords" element={<KeywordView />} />
          <Route path="/library/recycle" element={<ImageRecycle />} />
          <Route path="/crawler/cookies" element={<CrawlerCookie />} />
          <Route path="/crawler/tasks" element={<CrawlerTask />} />
          <Route path="/tagging" element={<ImageTagging />} />
          <Route path="/tagging/features" element={<FeatureManagement />} />
          <Route path="/tagging/data-cleaning" element={<DataCleaningTask />} />
          <Route path="/tagging/tagging-task" element={<TaggingTask />} />
          <Route path="/tagging/feature-analysis" element={<FeatureAnalysis />} />
          <Route path="/tagging/feature-groups" element={<FeatureGroupManagement />} />
          <Route path="/tagging/recycle" element={<ImageRecycle />} />
          <Route path="/tools/cleaning-test" element={<ImageCleaningTest />} />
          <Route path="/tools/tagging-test" element={<ImageTaggingTest />} />
          <Route path="/sample-set/management" element={<SampleSetManagement />} />
          <Route path="/sample-set/view" element={<SampleSetView />} />
          <Route path="/requirement/management" element={<RequirementManagement />} />
          <Route path="/requirement/progress/:id" element={<RequirementProgress />} />
          <Route path="/style/management" element={<StyleManagement />} />
          <Route path="/style/view" element={<StyleImageView />} />
          <Route path="/style/match" element={<StyleMatch />} />
          <Route path="/settings/directory" element={<SettingsDirectory />} />
        </Routes>
      </MainLayout>
    </Router>
  )
}

export default App

