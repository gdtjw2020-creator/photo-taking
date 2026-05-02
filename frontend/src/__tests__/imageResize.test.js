import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

const TEST_IMAGE_PATH = resolve(__dirname, '../../../微信图片_20240229123949.jpg')

// Real dimensions of the test image: 2160 x 2880 (maxEdge 2880 > 2560)
// Expected after resize: 1920 x 2560

// Helper to create mock browser environment
function setupMocks() {
  const mockImage = {
    width: 0,
    height: 0,
    onload: null,
    onerror: null,
    _src: null,
    set src(val) { this._src = val }
  }

  // Track created images to trigger onload
  const imageInstances = []

  vi.stubGlobal('Image', function() {
    const img = { ...mockImage }
    imageInstances.push(img)
    return img
  })

  vi.stubGlobal('URL', {
    ...URL,
    createObjectURL: vi.fn(() => 'blob:mock-url'),
    revokeObjectURL: vi.fn()
  })

  const mockCtx = {
    drawImage: vi.fn()
  }

  const mockCanvas = {
    width: 0,
    height: 0,
    getContext: vi.fn(() => mockCtx),
    toBlob: vi.fn((cb) => {
      // Create a tiny valid PNG as mock blob
      cb(new Uint8Array([0x89, 0x50, 0x4E, 0x47]))
    })
  }

  vi.spyOn(document, 'createElement').mockImplementation((tag) => {
    if (tag === 'canvas') return mockCanvas
    return document.createElement(tag)
  })

  return { imageInstances, mockCanvas, mockCtx }
}

describe('resizeImageIfNeeded', () => {
  let resizeImageIfNeeded, MAX_IMAGE_EDGE

  beforeAll(async () => {
    const mod = await import('../utils/imageResize.js')
    resizeImageIfNeeded = mod.resizeImageIfNeeded
    MAX_IMAGE_EDGE = mod.MAX_IMAGE_EDGE
  })

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('MAX_IMAGE_EDGE should be 2560', () => {
    expect(MAX_IMAGE_EDGE).toBe(2560)
  })

  it('should return non-image files unchanged', async () => {
    const file = new File(['test'], 'test.txt', { type: 'text/plain' })
    const result = await resizeImageIfNeeded(file)
    expect(result).toBe(file)
  })

  it('should return image unchanged when longest edge <= 2560', async () => {
    const { imageInstances } = setupMocks()
    const file = new File(['fake-img'], 'small.jpg', { type: 'image/jpeg' })

    const promise = resizeImageIfNeeded(file)

    // Simulate image loading with small dimensions
    const img = imageInstances[0]
    img.width = 1920
    img.height = 1080
    img.onload()

    const result = await promise
    expect(result).toBe(file)
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
  })

  it('should resize image when longest edge > 2560', async () => {
    const { imageInstances, mockCanvas } = setupMocks()
    const file = new File(['fake-img'], 'large.jpg', { type: 'image/jpeg' })

    const promise = resizeImageIfNeeded(file)

    const img = imageInstances[0]
    img.width = 2160
    img.height = 3840
    img.onload()

    const result = await promise

    // maxEdge = 3840, ratio = 2560/3840 = 2/3
    expect(mockCanvas.width).toBe(1440)   // 2160 * 2560/3840
    expect(mockCanvas.height).toBe(2560)  // 3840 * 2560/3840
    expect(result).not.toBe(file)
    expect(result.name).toBe('large.jpg')
    expect(result.type).toBe('image/jpeg')
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
  })

  it('should return original file on image load error', async () => {
    const { imageInstances } = setupMocks()
    const file = new File(['corrupt'], 'bad.jpg', { type: 'image/jpeg' })

    const promise = resizeImageIfNeeded(file)

    imageInstances[0].onerror()

    const result = await promise
    expect(result).toBe(file)
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
  })

  it('should handle portrait image where height is the longest edge', async () => {
    const { imageInstances, mockCanvas } = setupMocks()
    const file = new File(['fake-img'], 'portrait.jpg', { type: 'image/jpeg' })

    const promise = resizeImageIfNeeded(file)

    const img = imageInstances[0]
    img.width = 1080
    img.height = 3000
    img.onload()

    await promise

    // maxEdge = 3000, ratio = 2560/3000
    expect(mockCanvas.width).toBe(922)   // 1080 * 2560/3000 = 921.6 → 922
    expect(mockCanvas.height).toBe(2560) // 3000 * 2560/3000 = 2560
  })

  it('should handle landscape image where width is the longest edge', async () => {
    const { imageInstances, mockCanvas } = setupMocks()
    const file = new File(['fake-img'], 'landscape.jpg', { type: 'image/jpeg' })

    const promise = resizeImageIfNeeded(file)

    const img = imageInstances[0]
    img.width = 4000
    img.height = 2000
    img.onload()

    await promise

    // maxEdge = 4000, ratio = 2560/4000 = 0.64
    expect(mockCanvas.width).toBe(2560)  // 4000 * 2560/4000
    expect(mockCanvas.height).toBe(1280) // 2000 * 2560/4000
  })
})

describe('resizeImageIfNeeded with real image file', () => {
  let resizeImageIfNeeded

  beforeAll(async () => {
    const mod = await import('../utils/imageResize.js')
    resizeImageIfNeeded = mod.resizeImageIfNeeded
  })

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('should correctly calculate resize for 微信图片_20240229123949.jpg (2160×2880)', async () => {
    const { imageInstances, mockCanvas } = setupMocks()

    const imageBuffer = readFileSync(TEST_IMAGE_PATH)
    const file = new File([imageBuffer], '微信图片_20240229123949.jpg', { type: 'image/jpeg' })

    const promise = resizeImageIfNeeded(file)

    const img = imageInstances[0]
    // Simulate browser loading the real image dimensions
    img.width = 2160
    img.height = 2880
    img.onload()

    const result = await promise

    // Verify resize happened (maxEdge 2880 > 2560)
    const ratio = 2560 / 2880
    const expectedWidth = Math.round(2160 * ratio)
    const expectedHeight = Math.round(2880 * ratio)

    expect(expectedWidth).toBe(1920)
    expect(expectedHeight).toBe(2560)

    expect(mockCanvas.width).toBe(expectedWidth)
    expect(mockCanvas.height).toBe(expectedHeight)

    // Verify we got a resized file (not the original)
    expect(result).not.toBe(file)
    expect(result.name).toBe('微信图片_20240229123949.jpg')
    expect(result.type).toBe('image/jpeg')
  })
})
