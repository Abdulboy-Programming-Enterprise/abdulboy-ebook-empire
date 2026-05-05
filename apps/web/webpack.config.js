// =============================================================================
// WEBPACK DEVELOPMENT CONFIGURATION
// =============================================================================

const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');

const isProduction = process.env.NODE_ENV === 'production';

module.exports = {
  mode: isProduction ? 'production' : 'development',
  entry: {
    main: './scripts/main.js',
    auth: './scripts/auth.js',
    payment: './scripts/payment.js',
    chatbot: './scripts/chatbot.js',
    admin: './scripts/admin.js',
    bookReader: './scripts/book-reader.js',
  },
  output: {
    filename: isProduction ? 'js/[name].[contenthash].js' : 'js/[name].js',
    path: path.resolve(__dirname, 'dist'),
    publicPath: '/',
    clean: true,
  },
  module: {
    rules: [
      {
        test: /\.css$/,
        use: [
          isProduction ? MiniCssExtractPlugin.loader : 'style-loader',
          'css-loader',
          'postcss-loader',
        ],
      },
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env'],
          },
        },
      },
      {
        test: /\.(png|svg|jpg|jpeg|gif|webp)$/,
        type: 'asset/resource',
        generator: {
          filename: 'images/[name].[hash][ext]',
        },
      },
      {
        test: /\.(woff|woff2|eot|ttf|otf)$/,
        type: 'asset/resource',
        generator: {
          filename: 'fonts/[name].[hash][ext]',
        },
      },
      {
        test: /\.html$/,
        use: ['html-loader'],
      },
    ],
  },
  plugins: [
    new CleanWebpackPlugin(),
    new MiniCssExtractPlugin({
      filename: isProduction ? 'css/[name].[contenthash].css' : 'css/[name].css',
    }),
    new HtmlWebpackPlugin({
      template: './public/index.html',
      filename: 'index.html',
      chunks: ['main'],
    }),
    new HtmlWebpackPlugin({
      template: './public/ebook-site.html',
      filename: 'ebook-site.html',
      chunks: ['main', 'payment'],
    }),
    new HtmlWebpackPlugin({
      template: './public/login.html',
      filename: 'login.html',
      chunks: ['auth'],
    }),
    new HtmlWebpackPlugin({
      template: './public/signup.html',
      filename: 'signup.html',
      chunks: ['auth'],
    }),
    new HtmlWebpackPlugin({
      template: './public/user-dashboard.html',
      filename: 'user-dashboard.html',
      chunks: ['main', 'auth'],
    }),
    new CopyWebpackPlugin({
      patterns: [
        { from: 'public/assets', to: 'assets', noErrorOnMissing: true },
        { from: 'public/images', to: 'images', noErrorOnMissing: true },
        { from: 'manifest.json', to: 'manifest.json' },
        { from: 'sw.js', to: 'sw.js' },
        { from: 'robots.txt', to: 'robots.txt' },
        { from: '.htaccess', to: '.htaccess' },
      ],
    }),
  ],
  devServer: {
    static: {
      directory: path.join(__dirname, 'dist'),
    },
    compress: true,
    port: 3000,
    hot: true,
    historyApiFallback: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  resolve: {
    extensions: ['.js', '.json', '.css'],
    alias: {
      '@': path.resolve(__dirname, 'scripts'),
      '@styles': path.resolve(__dirname, 'styles'),
      '@components': path.resolve(__dirname, 'components'),
    },
  },
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
      },
    },
  },
  devtool: isProduction ? 'source-map' : 'eval-source-map',
};
