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
import LutFileManagement from './pages/LutFileManagement'
import SampleImageManagement from './pages/SampleImageManagement'
import SampleImageLutResults from './pages/SampleImageLutResults'
import LutAnalysisTest from './pages/LutAnalysisTest'
import LutClusterAnalysis from './pages/LutClusterAnalysis'
import LutClusterSnapshots from './pages/LutClusterSnapshots'
import ImageSimilarityTest from './pages/ImageSimilarityTest'
import ImageFeatureAnalysis from './pages/ImageFeatureAnalysis'
import SemanticSearch from './pages/SemanticSearch'
import SemanticSearchSettings from './pages/SemanticSearchSettings'

function App() {
  return (
    <Router>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Navigate to="/library/images" replace />} />
          <Route path="/library/images" element={<ImageLibrary />} />
          <Route path="/library/feature-analysis" element={<ImageFeatureAnalysis />} />
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
          <Route path="/tools/lut-analysis-test" element={<LutAnalysisTest />} />
          <Route path="/tools/image-similarity-test" element={<ImageSimilarityTest />} />
          <Route path="/sample-set/management" element={<SampleSetManagement />} />
          <Route path="/sample-set/view" element={<SampleSetView />} />
          <Route path="/requirement/management" element={<RequirementManagement />} />
          <Route path="/requirement/progress/:id" element={<RequirementProgress />} />
          <Route path="/style/management" element={<StyleManagement />} />
          <Route path="/style/view" element={<StyleImageView />} />
          <Route path="/style/match" element={<StyleMatch />} />
          <Route path="/lut-analysis/files" element={<LutFileManagement />} />
          <Route path="/lut-analysis/sample-images" element={<SampleImageManagement />} />
          <Route path="/lut-analysis/sample-images/:imageId/lut-results" element={<SampleImageLutResults />} />
          <Route path="/lut-analysis/cluster" element={<LutClusterAnalysis />} />
          <Route path="/lut-analysis/snapshots" element={<LutClusterSnapshots />} />
          <Route path="/semantic-search" element={<SemanticSearch />} />
          <Route path="/semantic-search/settings" element={<SemanticSearchSettings />} />
          <Route path="/settings/directory" element={<SettingsDirectory />} />
        </Routes>
      </MainLayout>
    </Router>
  )
}

export default App

