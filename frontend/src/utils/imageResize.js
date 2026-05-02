const MAX_IMAGE_EDGE = 2560

const resizeImageIfNeeded = (file) => {
  return new Promise((resolve, reject) => {
    if (!file.type.startsWith('image/')) {
      resolve(file)
      return
    }
    const img = new Image()
    const url = URL.createObjectURL(file)
    img.onload = () => {
      URL.revokeObjectURL(url)
      const maxEdge = Math.max(img.width, img.height)
      if (maxEdge <= MAX_IMAGE_EDGE) {
        resolve(file)
        return
      }
      const ratio = MAX_IMAGE_EDGE / maxEdge
      const newWidth = Math.round(img.width * ratio)
      const newHeight = Math.round(img.height * ratio)
      const canvas = document.createElement('canvas')
      canvas.width = newWidth
      canvas.height = newHeight
      const ctx = canvas.getContext('2d')
      ctx.drawImage(img, 0, 0, newWidth, newHeight)
      canvas.toBlob((blob) => {
        const resizedFile = new File([blob], file.name, { type: file.type })
        resolve(resizedFile)
      }, file.type)
    }
    img.onerror = () => {
      URL.revokeObjectURL(url)
      resolve(file)
    }
    img.src = url
  })
}

export { MAX_IMAGE_EDGE, resizeImageIfNeeded }
