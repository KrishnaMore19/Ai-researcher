export default function Loading() {
  console.log('LOADING TRIGGERED!')
  return (
    <div className="fixed inset-0 bg-red-500 flex items-center justify-center">
      <h1 className="text-white text-4xl">LOADING!</h1>
    </div>
  )
}