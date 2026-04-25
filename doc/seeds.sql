
-- 清理旧数据
TRUNCATE TABLE public.templates RESTART IDENTITY CASCADE;


INSERT INTO public.templates (name, preview_url, prompts, reference_image_url)
VALUES 
(
  '影楼婚纱', 
  'https://cdn.flashvideos.org/photoshoots/outputs/20260425/5d068c84-f0f4-4d92-848d-3b439df55086/553672e9-57a8-493c-bc8d-6f133f528f40.png?q=80&w=300&h=400&auto=format&fit=crop', 
  ARRAY[
    'Minimalist white background, French vintage wedding dress, standing sideways, holding white roses, looking back with a smile, soft lighting, facial features highly restoring the reference image character, maintaining identity consistency',
    'Minimalist white background, French vintage wedding dress, face close-up, eyes closed sniffing flower fragrance, long eyelashes, clear skin texture, precise replication of reference image features',
    'Minimalist white background, French vintage wedding dress, half-body sitting posture, hands folded on knees, noble and elegant, facial expressions highly unified with reference image',
    'Minimalist white background, French vintage wedding dress, full-view back profile, trailing long dress, looking back at the camera, side profile perfectly restoring reference image silhouette',
    'Minimalist white background, French vintage wedding dress, side profile silhouette, natural light by the window, dreamy halo, emotional portrait, maintaining face consistency'
  ],
  'https://cdn.flashvideos.org/photoshoots/outputs/20260425/5d068c84-f0f4-4d92-848d-3b439df55086/553672e9-57a8-493c-bc8d-6f133f528f40.png?q=80&w=1280'
),
(
  '旗袍韵味', 
  'https://images.unsplash.com/photo-1578301978018-3005759f48f7?q=80&w=300&h=400&auto=format&fit=crop', 
  ARRAY[
    'Chinese courtyard background, exquisite silk cheongsam, leaning against an ancient red pillar, holding a folding fan half-covering the face, elegant charm, facial features highly restoring reference image',
    'Chinese courtyard background, exquisite silk cheongsam, close-up shot, chin resting on hand looking into the distance, gentle and lovely, precise replication of reference image features',
    'Chinese courtyard background, exquisite silk cheongsam, strolling on flagstone road, holding a silk umbrella, graceful posture in the rain, maintaining face consistency in motion',
    'Chinese courtyard background, exquisite silk cheongsam, sitting sideways on a stone bench, adjusting hair hairpin, mottled light and shadow, facial expression restoring reference image',
    'Chinese courtyard background, exquisite silk cheongsam, full-view panoramic view, leaning against a carved window, quiet and beautiful, maintaining identity consistency'
  ],
  'https://images.unsplash.com/photo-1578301978018-3005759f48f7?q=80&w=1280'
),
(
  '职场精英', 
  'https://cdn.flashvideos.org/manual_transfer/179004c9-d2aa-4914-a75e-3a7d12dc03ea.png?q=80&w=300&h=400&auto=format&fit=crop', 
  ARRAY[
    'Modern office background, dark slim-fit suit, one hand on chin sitting at desk, firm and confident gaze, precise restoration of reference image facial features',
    'Modern office background, dark slim-fit suit, standing in front of floor-to-ceiling window, holding coffee cup looking outside, side profile highly restoring reference image',
    'Modern office background, dark slim-fit suit, front close-up, neat hairstyle, decent smile, maintaining identity completely consistent with reference image',
    'Modern office background, dark slim-fit suit, turning sideways adjusting cufflinks, focused expression, facial details precisely replicated',
    'Modern office background, dark slim-fit suit, walking through corridor with a tablet, confident pace, face consistency locked'
  ],
  'https://cdn.flashvideos.org/manual_transfer/179004c9-d2aa-4914-a75e-3a7d12dc03ea.png?q=80&w=1280'
),
(
  '海边落日', 
  'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=300&h=400&auto=format&fit=crop', 
  ARRAY[
    'Bali beach background, sunset afterglow golden light, holding skirt running by the waves and looking back, facial features highly restoring reference image',
    'Bali beach background, sunset afterglow golden light, sitting on the sand, fiddling with hair, backlighting outline, face expression consistent with reference image',
    'Bali beach background, sunset afterglow golden light, back to camera with arms open to the sea breeze, side profile perfectly restoring reference image',
    'Bali beach background, sunset afterglow golden light, close-up smile, face stained with fine sand, youthful vibe, maintaining identity consistency',
    'Bali beach background, sunset afterglow golden light, lying sideways in shallow water, sea water washing over dress hem, facial features precisely locked'
  ],
  'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1280'
),
(
  '赛博朋克', 
  'https://cdn.flashvideos.org/manual_transfer/023c9124-5d64-4f34-81de-7360adff9a5d.png?q=80&w=300&h=400&auto=format&fit=crop', 
  ARRAY[
    'Neon light background, futuristic techwear, holding laser props, squatting on the edge of the rooftop, cold gaze, facial features precisely restoring reference image',
    'Neon light background, futuristic techwear, side face close-up, colored neon light shadows, face details highly restoring reference image',
    'Neon light background, futuristic techwear, shuttling through busy night market streets, maintaining facial identity consistency in motion',
    'Neon light background, futuristic techwear, back view holding a katana, messy hair blowing, side profile precisely locking reference image character',
    'Neon light background, futuristic techwear, standing in front of a giant holographic projection, scattered light and shadow, maintaining complete consistency with reference image character'
  ],
  'https://cdn.flashvideos.org/manual_transfer/023c9124-5d64-4f34-81de-7360adff9a5d.png?q=80&w=1280'
);
