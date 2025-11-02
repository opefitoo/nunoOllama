# AI Chat Integration Guide

Complete guide to integrate the AI chat interface into your React Admin planning UI.

## Overview

The AI chat provides:
- **Interactive conversation** with AI about optimization failures
- **Real-time suggestions** with risk levels and implementation code
- **Quick action buttons** for common questions
- **Expandable suggestions** with detailed explanations
- **Reasoning traces** from DeepSeek showing AI's thinking process

## Setup Steps

### 1. Backend Setup

#### Add the AI router to FastAPI

Edit `/fastapi_app/main.py` and register the AI router:

```python
from fastapi_app.routers import planning_ai

# Add to your FastAPI app
app.include_router(planning_ai.router)
```

#### Add environment variable

Edit `/inur.django/.env`:

```bash
# AI Orchestrator Configuration
AI_ORCHESTRATOR_URL=http://localhost:8001
```

For Docker deployment:
```bash
AI_ORCHESTRATOR_URL=http://ai-planning:8001
```

### 2. Frontend Setup

#### Add environment variable

Edit `/nuno-react-admin/.env`:

```bash
# AI Orchestrator URL
VITE_AI_ORCHESTRATOR_URL=http://localhost:8001
```

#### Import the chat component

Add to your planning page (e.g., `src/pages/planning/MonthlyPlanningShow.tsx` or `planning-better.tsx`):

```typescript
import { OptimizerAIChat } from '../../components/OptimizerAIChat';
```

### 3. Integration Options

#### Option A: Add Chat Button to Planning Page

Add a floating action button that opens the chat:

```typescript
import { useState } from 'react';
import { Fab, Dialog, DialogContent } from '@mui/material';
import { Psychology as AIIcon } from '@mui/icons-material';
import { OptimizerAIChat } from '../../components/OptimizerAIChat';

export const MonthlyPlanningShow = () => {
  const [chatOpen, setChatOpen] = useState(false);
  const record = useRecordContext();

  return (
    <>
      {/* Your existing planning UI */}
      <div>
        {/* ... planning grid, calendar, etc ... */}
      </div>

      {/* AI Chat FAB */}
      <Fab
        color="secondary"
        aria-label="AI Assistant"
        onClick={() => setChatOpen(true)}
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        }}
      >
        <AIIcon />
      </Fab>

      {/* AI Chat Dialog */}
      <Dialog
        open={chatOpen}
        onClose={() => setChatOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogContent sx={{ p: 0 }}>
          <OptimizerAIChat
            planningId={record.id}
            month={record.month}
            year={record.year}
            failureMessage={null} // Pass optimizer failure message if available
            onClose={() => setChatOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </>
  );
};
```

#### Option B: Embed Chat in Sidebar

Add the chat as a permanent sidebar:

```typescript
import { Box, Grid } from '@mui/material';
import { OptimizerAIChat } from '../../components/OptimizerAIChat';

export const MonthlyPlanningShow = () => {
  const record = useRecordContext();

  return (
    <Grid container spacing={2}>
      {/* Main planning view */}
      <Grid item xs={12} md={8}>
        <div>
          {/* ... planning grid ... */}
        </div>
      </Grid>

      {/* AI Chat Sidebar */}
      <Grid item xs={12} md={4}>
        <Box sx={{ position: 'sticky', top: 16 }}>
          <OptimizerAIChat
            planningId={record.id}
            month={record.month}
            year={record.year}
          />
        </Box>
      </Grid>
    </Grid>
  );
};
```

#### Option C: Show After Optimization Failure

Automatically open chat when optimization fails:

```typescript
const handleOptimize = async () => {
  try {
    const result = await dataProvider.create('planning/optimize', {
      data: { planning_id: record.id }
    });

    if (!result.data.success) {
      // Optimization failed - open AI chat
      setFailureMessage(result.data.message);
      setChatOpen(true);
    }
  } catch (error) {
    notify('Erreur d\'optimisation', { type: 'error' });
  }
};

// In render:
<OptimizerAIChat
  planningId={record.id}
  month={record.month}
  year={record.year}
  failureMessage={failureMessage}  // Pass the failure message
  onClose={() => setChatOpen(false)}
/>
```

## Usage Examples

### Example 1: Quick Questions

User types: **"Pourquoi l'optimisation échoue?"**

AI responds with:
```
📊 Analyse Complète

Cause Racine:
Capacité insuffisante sur 5 jours critiques combinée avec
la contrainte stricte de weekends OFF

Problèmes Critiques:
• Écart de capacité de 1-2 employés les jours 1, 5, 12, 20, 28
• 2 stagiaires à l'école réduisant le pool disponible
• Contrainte de weekend retire 8 jours de l'espace d'optimisation

💡 Suggestions de Relaxation (par priorité):

#1 Couverture Quotidienne Minimale [RISQUE: FAIBLE]
   Stratégie: Permettre 2 employés au lieu de 3 les jours à faible demande
   Impact: Permettra à l'optimiseur de trouver une solution réalisable

#2 Jours Consécutifs de Travail [RISQUE: MOYEN]
   Stratégie: Permettre 6 jours consécutifs au lieu de 5
   Impact: Augmente la flexibilité de planification de 20%
```

### Example 2: Implementation Guidance

User clicks on suggestion #1 to expand:

Shows:
- ✅ Full description
- ✅ Implementation code snippet
- ✅ Expected impact details
- ✅ Risk assessment

User can copy the code directly!

### Example 3: Reasoning Trace (DeepSeek-reasoner)

Click "Voir le raisonnement" to see:
```
🤔 Raisonnement LLM:

Étape 1: Analysé les diagnostics de capacité
- Identifié 5 jours avec écart de capacité > 0
- Calculé: besoin = 3, disponible = 2, écart = 1

Étape 2: Examiné les contraintes de week-end
- 8 jours de week-end (4 samedis + 4 dimanches)
- Contrainte rigide: tous OFF le week-end
- Conflit: besoin de couverture vs contrainte OFF

Étape 3: Prioritisé les relaxations
- Risque FAIBLE: Réduire couverture min (2 au lieu de 3)
- Risque MOYEN: Assouplir jours consécutifs (6 au lieu de 5)
- Recommandé: Commencer par risque FAIBLE
```

## Quick Action Buttons

Pre-configured questions for common scenarios:

1. **"Pourquoi ça échoue?"** → Full diagnostic analysis
2. **"Suggère des solutions"** → Get prioritized relaxation suggestions
3. **"Analyse complète"** → Comprehensive review with recommendations

Users can click these for instant guidance without typing.

## Features

### Chat Interface
- ✅ Real-time conversation with AI
- ✅ Message history
- ✅ Typing indicators
- ✅ Auto-scroll to latest message
- ✅ Beautiful gradient design

### Suggestions Display
- ✅ Priority-ordered suggestions (1=highest)
- ✅ Risk level chips (LOW/MEDIUM/HIGH)
- ✅ Expandable details
- ✅ Implementation code snippets
- ✅ Expected impact descriptions

### Reasoning Transparency
- ✅ DeepSeek reasoning traces
- ✅ Step-by-step thinking process
- ✅ Collapsible for clean UI

## API Endpoints Used

The chat component uses these Django endpoints:

```typescript
// Full analysis with diagnostics
POST /planning/{planning_id}/ai-analysis
{
  "user_question": "Pourquoi l'optimisation échoue?",
  "failure_message": "No solution found (INFEASIBLE)"
}

// Quick advice (faster)
POST /planning/{planning_id}/ai-quick-advice
{
  "question": "Suggère des solutions",
  "failure_message": "INFEASIBLE"
}

// Check AI orchestrator status
GET /planning/ai-status
```

## Styling Customization

The chat uses Material-UI theming. Customize colors in the component:

```typescript
// Header gradient
background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'

// User message bubble
backgroundColor: '#667eea'

// Assistant message bubble
backgroundColor: 'white'

// Risk level colors
getRiskColor(risk: string) {
  switch (risk) {
    case 'low': return 'success';
    case 'medium': return 'warning';
    case 'high': return 'error';
  }
}
```

## Testing

### 1. Start Services

```bash
# Terminal 1: AI Orchestrator
cd /Users/mehdi/workspace/clients/inur-sur.lu/nuno/nunoAIPlanning
docker-compose up

# Terminal 2: Django backend
cd /Users/mehdi/workspace/clients/inur-sur.lu/nuno/inur.django
source venv/bin/activate
python manage.py runserver

# Terminal 3: React Admin
cd /Users/mehdi/workspace/clients/inur-sur.lu/nuno/nuno-react-admin
npm run dev
```

### 2. Test the Chat

1. Navigate to a planning page (e.g., http://localhost:5173/#/planning/monthly-planning/4/show)
2. Click the AI Assistant button (floating action button)
3. Chat opens
4. Try quick action: "Pourquoi ça échoue?"
5. Verify AI response appears
6. Click on a suggestion to expand details

### 3. Verify Backend

```bash
# Check AI orchestrator
curl http://localhost:8001/health

# Check Django AI endpoint
curl http://localhost:8000/planning/ai-status
```

## Troubleshooting

### Chat doesn't open
- ✅ Check console for errors
- ✅ Verify component is imported correctly
- ✅ Check dialog state is managed properly

### No AI response
- ✅ Check AI orchestrator is running: `docker ps`
- ✅ Verify environment variables are set
- ✅ Check Django logs for errors
- ✅ Test endpoints directly with curl

### Network errors
- ✅ Verify CORS settings in Django
- ✅ Check AI_ORCHESTRATOR_URL is correct
- ✅ Ensure both services can communicate

### Styling issues
- ✅ Check Material-UI theme is loaded
- ✅ Verify gradient CSS is supported
- ✅ Check z-index for dialogs/FABs

## Production Deployment

### Environment Variables

```bash
# .env.production for React Admin
VITE_AI_ORCHESTRATOR_URL=https://ai-orchestrator.yourdomain.com

# .env for Django
AI_ORCHESTRATOR_URL=http://ai-planning:8001
```

### Security

1. **Add authentication** to AI endpoints
2. **Rate limiting** on chat requests (prevent abuse)
3. **CORS configuration** for production domains
4. **API key rotation** for LLM provider

### Monitoring

Log all AI interactions for:
- Quality assessment
- Cost tracking
- User feedback analysis
- Model fine-tuning data

## Cost Optimization

- **Cache responses** for identical questions
- **Use quick-advice** for simple queries ($0.05 vs $0.50)
- **Batch analysis** for multiple plannings
- **Implement retry logic** with exponential backoff

## Next Steps

1. ✅ Deploy AI orchestrator service
2. ✅ Add chat to planning pages
3. ✅ Test with real planning failures
4. ✅ Collect user feedback
5. ✅ Fine-tune prompts based on usage
6. ✅ Add automated retry with AI suggestions

For full documentation, see `/Users/mehdi/workspace/clients/inur-sur.lu/nuno/nunoAIPlanning/README.md`
